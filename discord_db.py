# ================================================= #
#  Made by Infinite © 2026
#  GitHub: https://github.com/Infinite-Unknown
#  Updates: https://github.com/Infinite-Unknown/Exodus-POST_request_brute
#
#  Copyright (c) 2026 Infinite. All rights reserved.
#  Free to copy, edit, and distribute.
#  Just give credit: https://github.com/Infinite-Unknown
# ================================================= #

"""
Discord Webhook Database Module
Uses Discord channels as a makeshift database for saving/reading data.
Experimental feature for syncing account configs across devices.
"""

import requests
import json
import os
import re
from datetime import datetime
from ui import font

# Config file path
CONFIG_PATH = os.path.join(os.getcwd(), 'Input', 'discord_config.json')

def load_webhook_config():
    """Load Discord webhook configuration"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def save_webhook_config(webhook_url):
    """Save Discord webhook URL to config"""
    input_dir = os.path.join(os.getcwd(), 'Input')
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    config = {
        'webhook_url': webhook_url,
        'created': datetime.now().isoformat()
    }
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    return True

def send_to_discord(webhook_url, content, embed=None, files=None):
    """Send a message to Discord webhook"""
    payload = {}
    
    if content:
        payload['content'] = content
    
    if embed:
        payload['embeds'] = [embed]
    
    try:
        if files:
            multipart_data = {
                'payload_json': (None, json.dumps(payload), 'application/json')
            }
            multipart_data.update(files)
            response = requests.post(webhook_url, files=multipart_data)
        else:
            response = requests.post(webhook_url, json=payload)
            
        return response.status_code in [200, 204], response
    except Exception as e:
        return False, str(e)


def upload_account_to_discord(webhook_url, account_name, curl_content):
    """
    Upload an account config to Discord as a formatted message.
    Uses a special format that can be parsed when reading back.
    """
    # Create embed for nice formatting
    embed = {
        "title": f"📁 Account: {account_name}",
        "description": "Exodus Account Backup",
        "color": 5763719,  # Green color
        "fields": [
            {
                "name": "Account Name",
                "value": f"`{account_name}`",
                "inline": True
            },
            {
                "name": "Backup Time",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True
            }
        ],
        "footer": {
            "text": "Exodus Discord DB"
        }
    }
    
    # Send the embed first
    success, _ = send_to_discord(webhook_url, None, embed)
    
    if success:
        # Send cURL as file attachment
        files = {
            'file': (f'{account_name}.txt', curl_content, 'text/plain')
        }
        
        # Use a marker format that includes the file
        data_message = f"[EXODUS_DATA:{account_name}]"
        success, response = send_to_discord(webhook_url, data_message, files=files)
        return success
    
    return False

def backup_all_accounts(webhook_url):
    """Backup all accounts to Discord"""
    saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    
    if not os.path.exists(saved_dir):
        return 0, "No SavedRequests folder found"
    
    files = [f for f in os.listdir(saved_dir) if f.endswith('.txt')]
    
    if not files:
        return 0, "No accounts to backup"
    
    # Send header message
    header_embed = {
        "title": "🔄 Exodus Backup Started",
        "description": f"Backing up {len(files)} account(s)...",
        "color": 3447003,  # Blue
        "timestamp": datetime.now().isoformat()
    }
    send_to_discord(webhook_url, None, header_embed)
    
    success_count = 0
    for filename in files:
        account_name = os.path.splitext(filename)[0]
        file_path = os.path.join(saved_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                curl_content = f.read().strip()
            
            if upload_account_to_discord(webhook_url, account_name, curl_content):
                success_count += 1
                print(font(f" [✓] Backed up: {account_name}", color="green"))
            else:
                print(font(f" [✗] Failed: {account_name}", color="red"))
        except Exception as e:
            print(font(f" [✗] Error reading {account_name}: {e}", color="red"))
    
    # Send completion message
    complete_embed = {
        "title": "✅ Backup Complete",
        "description": f"Successfully backed up {success_count}/{len(files)} accounts",
        "color": 5763719 if success_count == len(files) else 15158332,
        "timestamp": datetime.now().isoformat()
    }
    send_to_discord(webhook_url, None, complete_embed)
    
    return success_count, f"Backed up {success_count}/{len(files)} accounts"

def send_otp_notification(webhook_url, otp, account_name="Unknown"):
    """Send OTP found notification to Discord"""
    embed = {
        "title": "🎉 OTP FOUND!",
        "description": f"Successfully found the OTP!",
        "color": 5763719,  # Green
        "fields": [
            {
                "name": "OTP",
                "value": f"**`{otp}`**",
                "inline": True
            },
            {
                "name": "Account",
                "value": account_name,
                "inline": True
            },
            {
                "name": "Time",
                "value": datetime.now().strftime("%H:%M:%S"),
                "inline": True
            }
        ],
        "footer": {
            "text": "Exodus Bruteforce"
        }
    }
    
    return send_to_discord(webhook_url, "@here OTP Found!", embed)

def test_webhook(webhook_url):
    """Test if the webhook is valid and working"""
    embed = {
        "title": "🔗 Exodus Connection Test",
        "description": "If you see this message, the webhook is working!",
        "color": 3447003,
        "timestamp": datetime.now().isoformat(),
        "footer": {
            "text": "Exodus Discord DB"
        }
    }
    
    return send_to_discord(webhook_url, None, embed)
