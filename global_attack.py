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

def send_webhook(webhook_url, content=None, embed=None, files=None):
    """Send message to Discord webhook"""
    payload = {}
    if content:
        payload['content'] = content
    if embed:
        payload['embeds'] = [embed]
    
    try:
        if files:
            # When sending files, payload must be sent as 'payload_json'
            multipart_data = {
                'payload_json': (None, json.dumps(payload), 'application/json')
            }
            multipart_data.update(files)
            response = requests.post(webhook_url, files=multipart_data)
        else:
            response = requests.post(webhook_url, json=payload)
            
        if response.status_code in [200, 204]:
            return True, response
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def register_user(data_webhook_url, username, password, curl_data, opt_in=True, notify_webhook_url=None, suppress_notification=False):
    """
    Register a new user to the global database.
    
    Args:
        ...
        suppress_notification: If True, skip sending the "New User" notification
    """
    password_hash = hash_password(password)
    
    # Create user data packet
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": curl_data,
        "opt_in": opt_in,
        "registered": datetime.now().isoformat()
    }
    
    encoded_data = json.dumps(user_data, indent=2)
    
    files = {
        'file': ('user_data.json', encoded_data, 'application/json')
    }
    
    data_message = f"[EXODUS_GLOBAL_USER:{username}]"
    success, error = send_webhook(data_webhook_url, content=data_message, files=files)
    
    if not success:
        return False, error
    
    # Send notification to public channel if provided and not suppressed
    if notify_webhook_url and not suppress_notification:
        embed = {
            "title": "👤 New User Joined",
            "description": f"**{username}** has joined the network!",
            "color": 5763719, # Green
            "fields": [
                {"name": "Status", "value": "Active" if opt_in else "Opted Out", "inline": True},
                {"name": "Joined", "value": f"<t:{int(time.time())}:R>", "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Exodus Global Network"}
        }
        send_webhook(notify_webhook_url, None, embed)
    
    trigger_dashboard_update()
    return True, None

def update_user_curl(data_webhook_url, username, password, new_curl, opt_in=True, notify_webhook_url=None, update_reason="Configuration Update"):
    """Update an existing user's cURL data and opt-in status"""
    password_hash = hash_password(password)
    
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": new_curl,
        "opt_in": opt_in,
        "updated": datetime.now().isoformat()
    }
    
    encoded_data = json.dumps(user_data, indent=2)
    
    files = {
        'file': ('user_data.json', encoded_data, 'application/json')
    }
    
    data_message = f"[EXODUS_GLOBAL_USER:{username}]"
    success, error = send_webhook(data_webhook_url, content=data_message, files=files)
    
    if not success:
        return False, error
    
    # Notification
    if notify_webhook_url:
        status_str = "Active" if opt_in else "Opted Out"
        embed = {
            "title": "🔄 Account Updated",
            "description": f"**{username}** updated their settings.",
            "color": 3447003, # Blue
            "fields": [
                {"name": "Update Type", "value": update_reason, "inline": True},
                {"name": "Status", "value": status_str, "inline": True},
                {"name": "Updated", "value": f"<t:{int(time.time())}:R>", "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Exodus Global Network"}
        }
        send_webhook(notify_webhook_url, None, embed)
    
    trigger_dashboard_update()
    return True, None

def update_user_status(data_webhook_url, username, password, curl_data, opt_in, notify_webhook_url=None):
    """Update just the opt-in status"""
    reason = "Opt-In" if opt_in else "Opt-Out"
    return update_user_curl(data_webhook_url, username, password, curl_data, opt_in, notify_webhook_url, update_reason=f"Status Change ({reason})")

def delete_discord_message(channel_id, message_id, bot_token):
    """Delete a specific message from Discord"""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
    headers = {
        "Authorization": f"Bot {bot_token}"
    }
    try:
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except:
        return False

def update_user_password(data_webhook_url, username, new_password, curl_data, opt_in=True, notify_webhook_url=None):
    """Update user password (creates new entry)"""
    # Suppress default registration notify, send custom one
    success, err = register_user(data_webhook_url, username, new_password, curl_data, opt_in, notify_webhook_url, suppress_notification=True)
    
    if success and notify_webhook_url:
        embed = {
            "title": "🔐 Security Update",
            "description": f"**{username}** changed their password.",
            "color": 15105570, # Orange
            "timestamp": datetime.now().isoformat()
        }
        send_webhook(notify_webhook_url, None, embed)
        
    return success, err

def rename_user(data_webhook_url, channel_id, bot_token, old_username, new_username, password, curl_data, old_message_id, opt_in=True):
    """
    Rename user:
    1. Register new username
    2. Delete old message
    """
    config = load_global_config() # Need notify webhook? Or passed? 
    # Wait, rename_user doesn't accept notify_webhook_url in signature normally?
    # I should add it or load it? Current signature didn't have it.
    # Let's check previous calls. They didn't pass it.
    # But I can try to load it from config if not passed, or leave it.
    # Actually, I should probably stick to signature or update it.
    # Let's check if I can grab it from global config.
    
    # 1. Register new (suppress notify)
    # Note: rename_user signature in menus.py doesn't pass notify url usually.
    # But register_user needs it if we were to notify.
    # Since I suppress it, I can pass None or anything.
    
    success, error = register_user(data_webhook_url, new_username, password, curl_data, opt_in, suppress_notification=True)
    if not success:
        return False, f"Failed to register new name: {error}"
    
    # 2. Delete old message
    if old_message_id:
        delete_discord_message(channel_id, old_message_id, bot_token)
        
    # Manual Notification for Rename?
    # I don't have the notify webhook url passed in here currently.
    # I can try to load it.
    try:
        cfg = load_global_config()
        notify_url = cfg.get('notify_webhook')
        if notify_url:
            embed = {
                "title": "📝 User Renamed",
                "description": f"**{old_username}** is now **{new_username}**",
                "color": 3447003,
                "timestamp": datetime.now().isoformat()
            }
            send_webhook(notify_url, None, embed)
    except:
        pass
            
    return True, None

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
    """Parse user data from Discord messages (supports file attachments)"""
    users = {}
    
    for msg in messages:
        # Check attachments first (new method)
        if msg.get('attachments'):
            for attachment in msg['attachments']:
                # Look for user_data.json or similar
                if attachment['filename'] == 'user_data.json' or attachment['filename'].endswith('.json'):
                    try:
                        # Download the file content
                        # Note: This increases network usage but is necessary for large files
                        resp = requests.get(attachment['url'])
                        if resp.status_code == 200:
                            user_data = resp.json()
                            username = user_data.get('username')
                            
                            if username and username not in users:
                                users[username] = user_data
                                users[username]['message_id'] = msg['id']
                    except:
                        continue
        
        # Fallback to old method (text content) for backward compatibility
        content = msg.get('content', '')
        if '[EXODUS_GLOBAL_USER]' in content and '[/EXODUS_GLOBAL_USER]' in content:
            try:
                start = content.find('[EXODUS_GLOBAL_USER]') + len('[EXODUS_GLOBAL_USER]')
                end = content.find('[/EXODUS_GLOBAL_USER]')
                json_str = content[start:end].strip()
                json_str = json_str.replace('```', '').strip()
                
                user_data = json.loads(json_str)
                username = user_data.get('username')
                
                if username and username not in users:
                    users[username] = user_data
                    users[username]['message_id'] = msg['id']
                        
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
        # Check participation status (default to True if not present)
        if not data.get('opt_in', True):
            continue
            
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

# === STATUS DASHBOARD FUNCTIONS ===

def init_status_dashboard(channel_id, bot_token):
    """
    Initialize the status dashboard message.
    Returns: (message_id, error)
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    embed = {
        "title": "📊 Exodus Global Status",
        "description": "Initializing dashboard...",
        "color": 3447003,
        "timestamp": datetime.now().isoformat(),
        "footer": {"text": "Live Status Board"}
    }
    
    payload = {
        "embeds": [embed]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['id'], None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)

def update_dashboard_display(channel_id, message_id, bot_token, users_dict):
    """Update the existing dashboard message with current user stats"""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    # Calculate stats
    total_users = len(users_dict)
    active_users = 0
    opted_out = 0
    
    # Text list of active users
    active_list = []
    
    sorted_users = sorted(users_dict.items())
    
    for username, data in sorted_users:
        if data.get('opt_in', True):
            active_users += 1
            # Add timestamp of last update if available?
            updated = data.get('updated') or data.get('registered')
            time_str = f"<t:{int(datetime.fromisoformat(updated).timestamp())}:R>" if updated else ""
            active_list.append(f"🟢 **{username}** {time_str}")
        else:
            opted_out += 1
            updated = data.get('updated') or data.get('registered')
            time_str = f"<t:{int(datetime.fromisoformat(updated).timestamp())}:R>" if updated else ""
            active_list.append(f"🔴 **{username}** (Opted Out) {time_str}")
            
    status_text = "\n".join(active_list) if active_list else "*No users found*"
    if len(status_text) > 3500: # Truncate if too long
        status_text = status_text[:3500] + "\n... (truncated)"
        
    embed = {
        "title": "📊 Exodus Global Status",
        "color": 3447003, # Blue
        "fields": [
            {"name": "Summary", "value": f"**Total:** {total_users} | **Active:** {active_users} | **Opted Out:** {opted_out}", "inline": False},
            {"name": "Operatives", "value": status_text, "inline": False}
        ],
        "timestamp": datetime.now().isoformat(),
        "footer": {"text": f"Last Updated • {datetime.now().strftime('%H:%M:%S')}"}
    }
    
    payload = {
        "embeds": [embed]
    }
    
    try:
        requests.patch(url, headers=headers, json=payload)
    except:
        pass

def trigger_dashboard_update():
    """Helper to trigger dashboard update using saved config"""
    try:
        config = load_global_config()
        if not config: return
        
        status_ch = config.get('status_channel_id')
        status_msg = config.get('status_message_id')
        bot_token = config.get('bot_token')
        data_ch = config.get('channel_id')
        
        if status_ch and status_msg and bot_token and data_ch:
            # We need to fetch users to update display
             messages, err = fetch_channel_messages(data_ch, bot_token)
             if not err:
                 users = parse_users_from_messages(messages)
                 update_dashboard_display(status_ch, status_msg, bot_token, users)
    except Exception:
        pass # Fail silently in background
