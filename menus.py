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

def auto_grab_curl(save_dest=None, login_data=None, headless=False):
    """
    Automatically captures cURL request using Playwright browser automation.
    Opens browser, user logs in and submits OTP, system captures the request.
    """
    if not headless:
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
    
    if not headless:
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
    
    if save_dest is None:
        input_dir = os.path.join(os.getcwd(), 'Input')
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
        save_path = os.path.join(input_dir, 'temp.txt')
    else:
        save_path = save_dest
    
    if not headless:
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
            
            
            # Use headless mode based on param
            headless_mode = headless
            
            # Try Chrome first (most common)
            try:
                browser = p.chromium.launch(headless=headless_mode, channel="chrome")
                browser_name = "Chrome"
            except Exception:
                pass
            
            # Fallback to Edge (comes pre-installed on Windows)
            if browser is None:
                try:
                    browser = p.chromium.launch(headless=headless_mode, channel="msedge")
                    browser_name = "Edge"
                except Exception:
                    pass
            
            # Last resort: use bundled Chromium
            if browser is None:
                if not headless:
                    print(ui.font(" [!] No Chrome/Edge found. Using bundled Chromium...", color="yellow"))
                browser = p.chromium.launch(headless=headless_mode)
                browser_name = "Chromium"
            else:
                if not headless:
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
                        if not headless:
                            print(ui.font("\n [SUCCESS] cURL request captured!", color="green", inverse=True))
            
            page.on("request", handle_request)
            
            if login_data:
                email = login_data.get('email')
                password = login_data.get('password')
                
                if not headless:
                    print(ui.font("\n [*] Automating login sequence...", color="cyan"))
                
                # Navigate to APSpace Login
                page.goto("https://apspace.apu.edu.my/login")
                
                # Click the "Log In" button on the APSpace landing page
                try:
                    page.wait_for_selector("text=Log In", timeout=10000)
                    page.locator("text=Log In").first.click()
                except Exception as e:
                    if not headless:
                        print(ui.font(f"\n [ERROR] Could not find the Log In button: {e}", color="red"))
                    captured_curl[0] = "ERROR"
                    browser.close()
                    return
                
                # Wait for Microsoft login page
                try:
                    # Enter Email
                    page.wait_for_selector("input[type='email']", timeout=15000)
                    page.fill("input[type='email']", email)
                    page.locator("input[type='submit']").first.click()
                    
                    # Enter Password
                    page.wait_for_selector("input[type='password']", timeout=15000)
                    page.fill("input[type='password']", password)
                    page.wait_for_timeout(1000)  # brief pause
                    page.locator("input[type='submit']").first.click()
                    
                    # Handle "Stay signed in?" prompt if it appears
                    try:
                        page.wait_for_selector("input[id='idBtn_Back']", timeout=5000) # "No" button
                        page.locator("input[id='idBtn_Back']").first.click()
                    except:
                        pass # Ignore if it doesn't appear
                        
                    if not headless:
                        print(ui.font(" [*] Login successful. Navigating to Attendix...", color="green"))
                        
                except Exception as e:
                    if not headless:
                        print(ui.font(f"\n [ERROR] Automated login failed: {e}", color="red"))
                    captured_curl[0] = "ERROR"
                    browser.close()
                    return

                # Navigate to Attendix Update
                page.goto(APSPACE_ATTENDIX_URL)
                
                # Inject a dummy OTP (000)
                try:
                    if not headless:
                        print(ui.font(" [*] Injecting OTP '000' and capturing request...", color="cyan"))
                        
                    # Wait for the OTP input fields to appear
                    page.wait_for_selector("input", timeout=15000)
                    page.wait_for_timeout(2000) # Give page time to fully initialize inputs
                    
                    # There are 3 inputs for the OTP. We fill them all with '0' and press Enter.
                    inputs = page.locator("input").element_handles()
                    if len(inputs) >= 3:
                        for i in range(3):
                            inputs[i].fill("0")
                            
                        # Press enter instantly on the last input to trigger verification
                        inputs[2].press("Enter")
                        
                except Exception as e:
                    if not headless:
                        print(ui.font(f"\n [ERROR] OTP injection failed: {e}", color="red"))
                    captured_curl[0] = "ERROR"
                    browser.close()
                    return
                    
            else:
                # Manual Flow
                # Navigate to APSpace
                page.goto(APSPACE_ATTENDIX_URL)
                
                print(ui.font("\n [*] Waiting for you to log in and submit an OTP...", color="yellow"))
                print(ui.font(" [*] (Browser will auto-close after capture)", color="yellow"))
            
            # Wait until we capture the request or user closes browser
            timeout_counter = 0
            while captured_curl[0] is None:
                try:
                    page.wait_for_timeout(500)  # Check every 500ms
                    timeout_counter += 1
                    # 60 second timeout for automated headless to prevent hanging
                    if headless and timeout_counter > 120:
                        captured_curl[0] = "ERROR"
                        break
                except:
                    break  # Browser was closed
            
            if captured_curl[0] == "ERROR":
                captured_curl[0] = None # Reset so it doesn't save "ERROR"
                
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
            
            
            if not headless:
                print(ui.font(f"\n [SUCCESS] cURL saved to: {save_path}", color="green", inverse=True))
                print(ui.font(" You can now use the bruteforce options!", color="cyan"))
        except Exception as e:
            if not headless:
                print(ui.font(f"\n [ERROR] Failed to save: {e}", color="red"))
                print(ui.font("\n Captured cURL (copy manually if needed):", color="yellow"))
                print(captured_curl[0])
    else:
        if not headless:
            print(ui.font("\n [!] No request was captured.", color="yellow"))
            print(ui.font(" Make sure you submitted an OTP on the Attendix page.", color="white"))
    
    if not headless:
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
            "",
            "0. Back"
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

            print(ui.font("\n Opening file browser...", color="green"))
            
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
            
        elif choice == "0":
            break
        else:
            print(ui.font(" Invalid Option. Please key in 1-5 or 0", color="red"))
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
            "",
            "0. Back"
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
            print(ui.font(" 0. Back", color="white"))
            
            select_choice = input("\n Input: ").strip().lower()
            
            if select_choice == "0":
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
                print(" 1. Add Account (Auto-Grab)")
                print(" 2. Add Account (Import File)")
                print(" 3. Rename Account")
                print(" 4. Delete Account")
                print(" 5. Manage Login Details")
                print("\n 0. Back")
                
                sub_choice = input("\n Input: ")
                
                if sub_choice == "1":
                    dest_name = input(" Enter new account name: ").strip()
                    if not dest_name:
                        print(ui.font(" Invalid name.", color="red"))
                        time.sleep(1)
                        continue
                    
                    if not dest_name.endswith(".txt"):
                        dest_name += ".txt"
                    
                    dest_path = os.path.join(saved_dir, dest_name)
                    
                    # Ask for login details
                    print(ui.font("\n Setup Auto-Login & Refresh? (Optional, but recommended)", color="cyan"))
                    print(" If you provide credentials, the app will auto-login and refresh the token on startup.")
                    setup_login = input(" Provide login details? (y/n): ").strip().lower()
                    
                    login_data = None
                    if setup_login == 'y':
                        email = input(" Enter APU Email: ").strip()
                        password = input(" Enter Password: ").strip()
                        
                        if email and password:
                            login_data = {'email': email, 'password': password}
                            
                            # Save login details
                            logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
                            if not os.path.exists(logins_dir):
                                os.makedirs(logins_dir)
                                
                            import json
                            login_file = os.path.join(logins_dir, f"{os.path.splitext(dest_name)[0]}.json")
                            try:
                                with open(login_file, 'w', encoding='utf-8') as f:
                                    json.dump(login_data, f)
                                print(ui.font(f" [SUCCESS] Login details saved for {os.path.splitext(dest_name)[0]}.", color="green"))
                            except Exception as e:
                                print(ui.font(f" [ERROR] Could not save login details: {e}", color="red"))
                        else:
                            print(ui.font(" [!] Missing email or password. Proceeding with manual login.", color="yellow"))
                            
                    auto_grab_curl(save_dest=dest_path, login_data=login_data)
                        
                elif sub_choice == "2":
                    print(ui.font("\n Opening file browser...", color="green"))
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
                        
                elif sub_choice == "3":
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
                    
                elif sub_choice == "4":
                    if not files:
                        print(ui.font(" No accounts to delete.", color="yellow"))
                        time.sleep(1)
                        continue
                        
                    print(ui.font("\n Enter account numbers separated by commas (e.g., 1,3,4):", color="yellow"))
                    print(ui.font(" Or enter a range (e.g., 1-5):", color="yellow"))
                    print(ui.font(" Or enter 'a' to delete ALL accounts.", color="red"))
                    selection = input(" Selection: ").strip().lower()
                    
                    if not selection:
                        continue
                        
                    selected_indices = set()
                    
                    if selection == 'a':
                        selected_indices = set(range(len(files)))
                    else:
                        try:
                            parts = selection.split(",")
                            for part in parts:
                                part = part.strip()
                                if "-" in part:
                                    start, end = part.split("-")
                                    for idx in range(int(start), int(end) + 1):
                                        if 1 <= idx <= len(files):
                                            selected_indices.add(idx - 1)
                                else:
                                    idx = int(part)
                                    if 1 <= idx <= len(files):
                                        selected_indices.add(idx - 1)
                        except ValueError:
                            print(ui.font("\n [!] Invalid input format.", color="red"))
                            time.sleep(1.5)
                            continue
                            
                    if not selected_indices:
                        print(ui.font("\n [!] No valid accounts selected.", color="red"))
                        time.sleep(1.5)
                        continue
                        
                    selected_files = [files[i] for i in sorted(selected_indices)]
                    
                    print(ui.font("\n Selected Accounts to Delete:", color="red", inverse=True))
                    for f in selected_files:
                        print(f"  • {os.path.splitext(f)[0]}")
                        
                    confirm = input(f"\n Delete {len(selected_files)} account(s)? (y/n): ").lower()
                    if confirm == 'y':
                        deleted_count = 0
                        for target in selected_files:
                            try:
                                os.remove(os.path.join(saved_dir, target))
                                deleted_count += 1
                            except Exception as e:
                                print(ui.font(f" [ERROR] Failed to delete {target}: {e}", color="red"))
                        print(ui.font(f" [SUCCESS] Deleted {deleted_count} account(s).", color="green"))
                    else:
                        print(" Cancelled.")
                    
                    time.sleep(1.5)
                    
                elif sub_choice == "5":
                    if not files:
                        print(ui.font(" No accounts available.", color="yellow"))
                        time.sleep(1)
                        continue
                        
                    try:
                        idx = int(input(" Enter number to manage login details: ")) - 1
                        if 0 <= idx < len(files):
                            target = files[idx]
                            account_name = os.path.splitext(target)[0]
                            
                            logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
                            if not os.path.exists(logins_dir):
                                os.makedirs(logins_dir)
                                
                            login_file = os.path.join(logins_dir, f"{account_name}.json")
                            import json
                            
                            if os.path.exists(login_file):
                                print(ui.font(f"\n Login details exist for {account_name}.", color="green"))
                                action = input(" Update (u) or Delete (d)?: ").strip().lower()
                                
                                if action == 'd':
                                    os.remove(login_file)
                                    print(ui.font(" [SUCCESS] Login details deleted.", color="green"))
                                elif action == 'u':
                                    email = input(" Enter new APU Email: ").strip()
                                    password = input(" Enter new Password: ").strip()
                                    
                                    if email and password:
                                        with open(login_file, 'w', encoding='utf-8') as f:
                                            json.dump({'email': email, 'password': password}, f)
                                        print(ui.font(" [SUCCESS] Login details updated.", color="green"))
                                    else:
                                        print(ui.font(" [!] Invalid input.", color="red"))
                            else:
                                print(ui.font(f"\n No login details found for {account_name}.", color="yellow"))
                                action = input(" Add login details? (y/n): ").strip().lower()
                                
                                if action == 'y':
                                    email = input(" Enter APU Email: ").strip()
                                    password = input(" Enter Password: ").strip()
                                    
                                    if email and password:
                                        with open(login_file, 'w', encoding='utf-8') as f:
                                            json.dump({'email': email, 'password': password}, f)
                                        print(ui.font(" [SUCCESS] Login details saved.", color="green"))
                                    else:
                                        print(ui.font(" [!] Invalid input.", color="red"))
                                        
                        else:
                            print(" Invalid number.")
                    except ValueError:
                        print(" Invalid input.")
                    time.sleep(1.5)
                    
                elif sub_choice == "0":
                    break
            
        elif choice == "0":
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
            "",
            "0. Back"
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
            
        elif choice == "0":
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

def global_attack_admin_menu():
    """Global Attack Admin Menu - Setup and Control"""
    while True:
        ui.clear()
        print(ui.font("       - Global Attack (Admin) -       \n", color="red", inverse=True))
        
        # Check current session
        config = global_attack.load_global_config()
        has_setup = config and config.get('data_webhook') and config.get('channel_id') and config.get('bot_token')
        
        if has_setup:
            print(ui.font(" [✓] Discord configured", color="green"))
        else:
            print(ui.font(" [!] Discord not configured", color="yellow"))
        ui.enter_effect([
            "",
            "1. Setup Discord",
            "2. Start Global Attack",
            "3. Manage Classes",
            "4. View Connected Users",
            "5. Setup Status Dashboard",
            "6. Remote Control (Bot Mode)",
            "",
            "0. Back"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "3":
            # Manage Classes
            if not has_setup:
                 print(ui.font("\n [!] Setup Discord first", color="yellow"))
                 time.sleep(1.5)
                 continue
                 
            while True:
                ui.clear()
                print(ui.font(" Manage Classes ", color="cyan", inverse=True))
                
                print(ui.font(" Fetching classes...", color="cyan"))
                classes, msg_id = global_attack.fetch_classes(config['channel_id'], config['bot_token'])
                
                print(f"\n Current Classes: {len(classes)}")
                if classes:
                    for i, c in enumerate(classes):
                        print(f"  {i+1}. {c}")
                else:
                    print("  (None)")
                    
                print("\n" + "-"*30)
                print(" 1. Add Class")
                print(" 2. Delete Class")
                print("\n 0. Back")
                
                sub = input("\n Input: ")
                
                if sub == "1":
                    name = input(" Enter Class Name: ").strip()
                    if name:
                        if name in classes:
                            print(ui.font(" [!] Class already exists", color="yellow"))
                        else:
                            classes.append(name)
                            if global_attack.save_classes(config['channel_id'], config['bot_token'], classes, msg_id):
                                print(ui.font(f" [SUCCESS] Added {name}", color="green"))
                            else:
                                print(ui.font(" [ERROR] Failed to save", color="red"))
                    time.sleep(1)
                    
                elif sub == "2":
                    if not classes:
                        continue
                    try:
                        idx = int(input(" Delete Number: ")) - 1
                        if 0 <= idx < len(classes):
                            removed = classes.pop(idx)
                            if global_attack.save_classes(config['channel_id'], config['bot_token'], classes, msg_id):
                                print(ui.font(f" [SUCCESS] Deleted {removed}", color="green"))
                            else:
                                print(ui.font(" [ERROR] Failed to save", color="red"))
                        else:
                            print(" Invalid number")
                    except:
                        pass
                    time.sleep(1)
                    
                elif sub == "0":
                    break
        
        elif choice == "1":
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
            
        elif choice == "5":
            # Setup Status Dashboard
            if not has_setup:
                 print(ui.font("\n [!] Setup Discord first", color="yellow"))
                 time.sleep(1.5)
                 continue
                 
            ui.clear()
            print(ui.font(" Setup Live Status Dashboard ", color="magenta", inverse=True))
            print("\n This creates a persistent message that updates in real-time.")
            print(" You can use a new channel or the Notify channel.\n")
            
            dashboard_cid = input(f" Dashboard Channel ID (default {config['channel_id']}): ").strip()
            if not dashboard_cid:
                dashboard_cid = config['channel_id']
                
            print(ui.font("\n Initializing dashboard...", color="cyan"))
            msg_id, err = global_attack.init_status_dashboard(dashboard_cid, config['bot_token'])
            
            if msg_id:
                config['status_channel_id'] = dashboard_cid
                config['status_message_id'] = msg_id
                global_attack.save_global_config(config)
                
                print(ui.font(f" [SUCCESS] Dashboard created! (ID: {msg_id})", color="green", inverse=True))
                
                # Trigger initial population
                print(ui.font(" Populating data...", color="cyan"))
                global_attack.trigger_dashboard_update()
            else:
                print(ui.font(f" [ERROR] Failed: {err}", color="red"))
            
            time.sleep(2)

        elif choice == "6":
            # Remote Control (Bot Mode)
            if not has_setup:
                 print(ui.font("\n [!] Setup Discord first", color="yellow"))
                 time.sleep(1.5)
                 continue

            ui.clear()
            print(ui.font(" Remote Control (Bot Mode) ", color="magenta", inverse=True))
            print("\n Setup command control (!start, !stop) via Discord.")
            print(" You need:")
            print(" 1. Server (Guild) ID")
            print(" 2. Admin Role ID (to restrict usage)\n")
            
            # Load or ask for Guild/Role/Channel
            guild_id = config.get('guild_id', '')
            admin_role_id = config.get('admin_role_id', '')
            control_channel_id = config.get('control_channel_id', config.get('channel_id'))
            
            if not guild_id:
                guild_id = input(" Enter Guild (Server) ID: ").strip()
            else:
                 print(f" Guild ID: {guild_id}")
                 change = input(" Change? (y/n): ").lower()
                 if change == 'y':
                     guild_id = input(" Enter Guild ID: ").strip()

            if not admin_role_id:
                admin_role_id = input(" Enter Admin Role ID: ").strip()
            else:
                 print(f" Role ID: {admin_role_id}")
                 change = input(" Change? (y/n): ").lower()
                 if change == 'y':
                     admin_role_id = input(" Enter Admin Role ID: ").strip()
                     
            print(f" Control Channel ID (where you type !start): {control_channel_id}")
            change = input(" Change? (y/n): ").lower()
            if change == 'y':
                 control_channel_id = input(" Enter Control Channel ID: ").strip()
            
            if guild_id and admin_role_id and control_channel_id:
                config['guild_id'] = guild_id
                config['admin_role_id'] = admin_role_id
                config['control_channel_id'] = control_channel_id
                global_attack.save_global_config(config)
                
                # Enter Listening Mode
                global_attack.listen_for_commands(
                    config['bot_token'], 
                    control_channel_id, 
                    guild_id, 
                    admin_role_id
                )
            else:
                print(ui.font("\n [!] Setup cancelled (missing ID).", color="red"))
                time.sleep(1.5)
            
        elif choice == "2":
            # Start Global Attack
            # Reuse logic since we can't easily import from here without circular deps if we moved it, 
            # but we are in menus.py so it's fine.
            # We need to make sure 'config' is loaded.
            if not has_setup:
                 print(ui.font("\n [!] Setup Discord first", color="yellow"))
                 time.sleep(1.5)
                 continue

            initiator = config.get('logged_in_user') or "Admin"

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
            
            # Select target
            ui.clear()
            print(ui.font(" Target Selection ", color="red", inverse=True))
            print("\n 1. Attack with ALL Users")
            print(" 2. Attack with Specific CLASS")
            print("\n 0. Back")
            
            target_choice = input("\n Input: ")
            
            if target_choice == "0":
                continue
            
            target_class = None
            if target_choice == "2":
                print(ui.font("\n Fetching classes...", color="cyan"))
                classes, _ = global_attack.fetch_classes(config['channel_id'], config['bot_token'])
                if not classes:
                    print(ui.font(" [!] No classes found.", color="yellow"))
                    time.sleep(2)
                    continue
                    
                print("\n Select Class:")
                for i, c in enumerate(classes):
                    print(f"  {i+1}. {c}")
                try:
                    c_idx = int(input(" Input: ")) - 1
                    if 0 <= c_idx < len(classes):
                        target_class = classes[c_idx]
                    else:
                        print(" Invalid.")
                        continue
                except:
                    continue
            
            # Filter active users manually to count them
            active_users = []
            total_users = len(users)
            
            for username, data in users.items():
                if data.get('opt_in', True):
                    # Check class if selected
                    if target_class and data.get('class_name') != target_class:
                        continue
                        
                    curl_data = data.get('curl_data')
                    if curl_data:
                        active_users.append({
                            'username': username,
                            'curl': curl_data
                        })
            
            if not active_users:
                print(ui.font(" [!] No ACTIVE users found for target.", color="yellow"))
                if total_users > 0:
                    print(f" (Found {total_users} users, but all are opted out)")
                time.sleep(2)
                continue
            
            print(ui.font(f"\n Found {len(active_users)} Users ready:", color="green"))
            for u in active_users:
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
            
            # Notify Discord
            notify_webhook = config.get('notify_webhook') or config.get('data_webhook')
            global_attack.send_attack_notification(
                notify_webhook, 
                initiator, 
                len(active_users)
            )
            
            # Prepare files
            temp_dir = os.path.join(os.getcwd(), 'Input', 'GlobalTemp')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            
            temp_files = []
            for u in active_users:
                filename = f"{u['username']}.txt"
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(u['curl'])
                temp_files.append(filename)
            
            print(ui.font("\n GLOBAL ATTACK STARTED!", color="red", inverse=True))
            print(ui.font(" Press 'q' or 'esc' to stop all attacks.\n", color="yellow"))
            
            ui.bg()
            attacker.run_global_attack(temp_files, temp_dir, num_threads, cooldown, notify_webhook)
            ui.bg_end()
            
        elif choice == "4":
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
                
                # Sort alphabetically
                sorted_users = sorted(users.items())
                
                for i, (username, data) in enumerate(sorted_users):
                    status = ""
                    if not data.get('opt_in', True):
                        status = ui.font(" (OPTED OUT)", color="red")
                    else:
                        status = ui.font(" (ACTIVE)", color="green")
                        
                    class_info = f" [{data.get('class_name')}]" if data.get('class_name') else ""
                        
                    print(f"  {i+1}. {username}{class_info}{status}")
            
            input("\n Press Enter to continue...")
            
        elif choice == "0":
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

def global_attack_user_menu():
    """Global Attack User Menu - Join and Update"""
    while True:
        ui.clear()
        print(ui.font("       - Global Attack (Join) -       \n", color="magenta", inverse=True))
        
        config = global_attack.load_global_config()
        logged_in = config and config.get('logged_in_user')
        has_setup = config and config.get('data_webhook')
        
        # Helper variables
        is_opted_in = True
        user_data = None
        
        if logged_in:
            try:
                messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
                if not err:
                    users = global_attack.parse_users_from_messages(messages)
                    user_data = users.get(config['logged_in_user'])
                    if user_data:
                        is_opted_in = user_data.get('opt_in', True)
            except:
                pass
            
            status_str = "ACTIVE" if is_opted_in else "OPTED OUT"
            status_color = "green" if is_opted_in else "red"
            
            class_display = f" | Class: {user_data.get('class_name')}" if user_data and user_data.get('class_name') else ""
            
            print(ui.font(f" Logged in as: {config['logged_in_user']}", color="green") + class_display)
            print(" Status: " + ui.font(status_str, color=status_color))
        else:
            print(ui.font(" Not logged in", color="yellow"))
            
        if not has_setup:
             print(ui.font(" [!] Network not configured (Requires Admin Setup)", color="red"))
        
        # Build Options
        options = []
        if not logged_in:
            options = ["1. Register Account", "2. Login", "", "0. Back"]
        else:
            current_class = user_data.get('class_name') if user_data else None
            class_status = f" [{current_class}]" if current_class else ""
            
            options = [
                "1. Manage Account", 
                f"2. {'Opt Out' if is_opted_in else 'Opt In'} (Toggle)", 
                f"3. Join Class{class_status}",
                "4. Leave Class",
                "5. Logout", 
                "",
                "0. Back"
            ]
            
        ui.enter_effect([
            "",
            *(options[:-1]),
            options[-1]
        ], delay=0.02, symbol="█")
        
        choice = input("\nInput: ")
        
        if not logged_in:
            # === NOT LOGGED IN OPTIONS ===
            if choice == "1":
                # Register
                if not has_setup:
                    print(ui.font("\n [!] Connection not configured.", color="red"))
                    time.sleep(1.5)
                    continue
                    
                ui.clear()
                print(ui.font(" Register New Account ", color="green", inverse=True))
                
                username = input("\n Username: ").strip()
                if not username or len(username) < 3:
                    print(ui.font(" [ERROR] Username must be at least 3 characters", color="red"))
                    time.sleep(1.5)
                    continue
                
                # Check if username exists
                print(ui.font(" Checking availability...", color="cyan"))
                messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
                if err:
                    print(ui.font(f" [ERROR] Connection failed: {err}", color="red"))
                    time.sleep(2)
                    continue
                
                existing_users = global_attack.parse_users_from_messages(messages)
                if username in existing_users:
                    print(ui.font(f" [ERROR] Username '{username}' is already taken.", color="red"))
                    time.sleep(2)
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
                print(ui.font(" Opening file browser...", color="green"))
                
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
                
                print(ui.font("\n Registering...", color="cyan"))
                success, error_msg = global_attack.register_user(
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
                    print(ui.font(f" [ERROR] Registration failed: {error_msg}", color="red"))
                
                time.sleep(2)
                
            elif choice == "2":
                # Login
                if not has_setup:
                    print(ui.font("\n [!] Connection not configured.", color="red"))
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
                
            elif choice == "0":
                break
            else:
                print(ui.font(" Invalid Option.", color="red"))
                time.sleep(1)
                
        else:
            # === LOGGED IN OPTIONS ===
            if choice == "1":
                # MANAGE ACCOUNT SUBMENU
                while True:
                    ui.clear()
                    print(ui.font(" Manage Global Account ", color="magenta", inverse=True))
                    print(f" Current User: {config['logged_in_user']}\n")
                    
                    ui.enter_effect([
                        "1. Change Username",
                        "2. Change Password",
                        "3. Update cURL",
                        "",
                        "0. Back"
                    ], delay=0.02, symbol="█")
                    
                    sub_choice = input("\n Input: ")
                    
                    if sub_choice == "1":
                        # Rename User
                        ui.clear()
                        print(ui.font(" Change Username ", color="cyan", inverse=True))
                        
                        new_name = input(" Enter new username: ").strip()
                        if len(new_name) < 3:
                            print(ui.font(" [ERROR] Must be at least 3 chars long.", color="red"))
                            time.sleep(1.5)
                            continue
                        
                        confirm = input(f" Confirm rename to '{new_name}'? (y/n): ").lower()
                        if confirm != 'y':
                            continue
                            
                        # Need to find old message ID first
                        print(ui.font("\n Locating account...", color="cyan"))
                        messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
                        if err:
                            print(ui.font(f" [ERROR] {err}", color="red"))
                            time.sleep(2)
                            continue
                            
                        users = global_attack.parse_users_from_messages(messages)
                        user_data = users.get(config['logged_in_user'])
                        
                        if not user_data:
                            print(ui.font(" [ERROR] Could not find your account in database.", color="red"))
                            time.sleep(2)
                            continue
                        
                        old_msg_id = user_data.get('message_id')
                        curl_data = user_data.get('curl_data', '') # Preserve cURL
                        # Preserve opt_in status
                        current_opt_in = user_data.get('opt_in', True)
                        
                        print(ui.font(" Updating...", color="cyan"))
                        # Note: rename_user doesn't support opt_in param efficiently without modifying it too?
                        # Wait, rename_user calls register_user. register_user makes a NEW entry.
                        # I should update register_user or manually handle opt_in passing in rename_user?
                        # register_user defaults opt_in=True.
                        # Let's check rename_user implementation.
                        # rename_user calls register_user.
                        # I need to ensure opt_in is preserved.
                        # But register_user just puts "opt_in": True hardcoded?
                        # Let's check global_attack.py
                        
                        # In global_attack.py:
                        # def register_user(..., opt_in=True): ... user_data = { ... "opt_in": opt_in ... }
                        # I only modified register_user to include "opt_in": True in the dictionary, I didn't add it as a parameter!
                        # Ah, I added `opt_in=True` to `update_user_curl` but NOT `register_user` arguments?
                        # Let's check my previous edit to global_attack.py.
                        # I see I changed register_user lines but I didn't see the arguments change in the diff?
                        # Line 69 was: def register_user(data_webhook_url, username, password, curl_data, notify_webhook_url=None):
                        # I didn't change the signature in the diff I saw earlier. I only added "opt_in": True to the dict.
                        # So rename_user calling register_user will invoke it with default True.
                        # So renaming WILL RESET opt-in status to True.
                        # This is a bug I introduced or didn't address.
                        # However, for this step, I'm just reverting menus.py. I can fix global_attack.py separately or now.
                        # Let's fix menus.py first.
                        
                        success, err = global_attack.rename_user(
                            config['data_webhook'],
                            config['channel_id'],
                            config['bot_token'],
                            config['logged_in_user'],
                            new_name,
                            config['logged_in_pass'],
                            curl_data,
                            old_msg_id,
                            opt_in=current_opt_in
                        )
                        
                        if success:
                            config['logged_in_user'] = new_name
                            global_attack.save_global_config(config)
                            print(ui.font(f"\n [SUCCESS] Username changed to {new_name}", color="green", inverse=True))
                            if err: # Warning about delete fail
                                print(ui.font(f" [WARNING] {err}", color="yellow"))
                        else:
                            print(ui.font(f" [ERROR] Rename failed: {err}", color="red"))
                        time.sleep(2)
                        
                    elif sub_choice == "2":
                        # Change Password
                        ui.clear()
                        print(ui.font(" Change Password ", color="cyan", inverse=True))
                        
                        new_pass = input(" New Password: ").strip()
                        if len(new_pass) < 4:
                            print(ui.font(" [ERROR] Must be at least 4 chars long.", color="red"))
                            time.sleep(1.5)
                            continue
                            
                        confirm_pass = input(" Confirm Password: ").strip()
                        if new_pass != confirm_pass:
                            print(ui.font(" [ERROR] Passwords don't match.", color="red"))
                            time.sleep(1.5)
                            continue
                            
                        # Need cURL data to re-register
                        print(ui.font("\n Fetching current data...", color="cyan"))
                        messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
                        if err:
                            print(ui.font(f" [ERROR] {err}", color="red"))
                            time.sleep(2)
                            continue
                            
                        users = global_attack.parse_users_from_messages(messages)
                        user_data = users.get(config['logged_in_user'])
                        
                        if not user_data:
                            print(ui.font(" [ERROR] Account not found.", color="red"))
                            time.sleep(2)
                            continue
                            
                        curl_data = user_data.get('curl_data', '')
                        
                        print(ui.font(" Updating password...", color="cyan"))
                        # Similar issue with password update? 
                        # update_user_password calls register_user.
                        # So it will also reset opt-in.
                        success, err = global_attack.update_user_password(
                            config['data_webhook'],
                            config['logged_in_user'],
                            new_pass,
                            curl_data,
                            opt_in=user_data.get('opt_in', True),
                            notify_webhook_url=config.get('notify_webhook')
                        )
                        
                        if success:
                            config['logged_in_pass'] = new_pass
                            global_attack.save_global_config(config)
                            print(ui.font("\n [SUCCESS] Password updated!", color="green", inverse=True))
                        else:
                            print(ui.font(f" [ERROR] Failed: {err}", color="red"))
                        time.sleep(2)
                        
                    elif sub_choice == "3":
                        # Update cURL
                        ui.clear()
                        print(ui.font(" Update cURL ", color="cyan", inverse=True))
                        print(ui.font(" Opening file browser...", color="green"))
                        
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
                        # For update_user_curl, I DID update the signature to accept opt_in.
                        # But I need to pass it here if I want to preserve it.
                        # Since I'm removing the fetch logic from this menu, I don't know the current status!
                        # So I might default to True or I need to fetch it again inside here?
                        # Or I just pass True (default) and assume active?
                        # Ideally, I should fetch it.
                        
                        # Fetching to get current status
                        messages, err = global_attack.fetch_channel_messages(config['channel_id'], config['bot_token'])
                        is_opted_in = True
                        if not err:
                            users = global_attack.parse_users_from_messages(messages)
                            ud = users.get(config['logged_in_user'])
                            if ud:
                                is_opted_in = ud.get('opt_in', True)

                        success, error_msg = global_attack.update_user_curl(
                            config['data_webhook'], 
                            config['logged_in_user'], 
                            config['logged_in_pass'], 
                            curl_data,
                            is_opted_in,
                            config.get('notify_webhook')
                        )
                        
                        if success:
                            print(ui.font(" [SUCCESS] cURL updated!", color="green", inverse=True))
                        else:
                            print(ui.font(f" [ERROR] Update failed: {error_msg}", color="red"))
                        
                        time.sleep(2)
                    
                    elif sub_choice == "0":
                        break
                    else:
                        print(ui.font(" Invalid Option.", color="red"))
                        time.sleep(1)

                
            elif choice == "2":
                # Toggle Opt-In/Out
                new_status = not is_opted_in
                print(ui.font(f"\n Changing status to {'ACTIVE' if new_status else 'OPTED OUT'}...", color="cyan"))
                
                if not user_data:
                     print(ui.font(" [ERROR] Could not fetch user data. Try again.", color="red"))
                     time.sleep(2)
                     continue
                     
                curl_data = user_data.get('curl_data', '')
                success, err = global_attack.update_user_status(
                    config['data_webhook'],
                    config['logged_in_user'],
                    config['logged_in_pass'],
                    curl_data,
                    new_status,
                    config.get('notify_webhook')
                )
                
                if success:
                    print(ui.font(f" [SUCCESS] Status updated!", color="green", inverse=True))
                else:
                    print(ui.font(f" [ERROR] Update failed: {err}", color="red"))
                time.sleep(1.5)

            elif choice == "3":
                # Join Class
                ui.clear()
                print(ui.font(" Join Class ", color="cyan", inverse=True))
                
                print(ui.font("\n Fetching classes...", color="cyan"))
                classes, _ = global_attack.fetch_classes(config['channel_id'], config['bot_token'])
                
                if not classes:
                    print(ui.font(" [!] No classes available.", color="yellow"))
                    time.sleep(2)
                    continue
                    
                print(f" Current Class: {user_data.get('class_name') if user_data else 'None'}\n")
                
                for i, c in enumerate(classes):
                    print(f"  {i+1}. {c}")
                    
                print("\n 0. Back")
                
                sel = input("\n Select Class: ").strip()
                if sel == '0':
                    continue
                    
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(classes):
                        new_class = classes[idx]
                        if user_data and user_data.get('class_name') == new_class:
                             print(ui.font(" [!] You are already in this class.", color="yellow"))
                             time.sleep(1.5)
                             continue
                             
                        print(ui.font(f"\n Joining '{new_class}'...", color="cyan"))
                        
                        # Preserve other data
                        curl_data = user_data.get('curl_data', '')
                        opt_in = user_data.get('opt_in', True)
                        
                        success, err = global_attack.update_user_class(
                            config['data_webhook'],
                            config['logged_in_user'],
                            config['logged_in_pass'],
                            curl_data,
                            new_class,
                            opt_in,
                            config.get('notify_webhook')
                        )
                        
                        if success:
                            print(ui.font(f" [SUCCESS] Joined {new_class}!", color="green"))
                        else:
                            print(ui.font(f" [ERROR] Failed: {err}", color="red"))
                    else:
                        print(" Invalid selection.")
                except ValueError:
                    print(" Invalid input.")
                time.sleep(1.5)

            elif choice == "4":
                # Leave Class
                if user_data and not user_data.get('class_name'):
                     print(ui.font("\n [!] You are not in any class.", color="yellow"))
                     time.sleep(1.5)
                     continue
                     
                confirm = input(f"\n Leave class '{user_data.get('class_name')}'? (y/n): ").lower()
                if confirm == 'y':
                    print(ui.font("\n Leaving class...", color="cyan"))
                    
                    curl_data = user_data.get('curl_data', '')
                    opt_in = user_data.get('opt_in', True)
                    
                    success, err = global_attack.update_user_class(
                        config['data_webhook'],
                        config['logged_in_user'],
                        config['logged_in_pass'],
                        curl_data,
                        None, # Remove class
                        opt_in,
                        config.get('notify_webhook')
                    )
                    
                    if success:
                        print(ui.font(" [SUCCESS] Left class.", color="green"))
                    else:
                        print(ui.font(f" [ERROR] Failed: {err}", color="red"))
                    time.sleep(1.5)

            elif choice == "5":
                # Logout
                config['logged_in_user'] = None
                config['logged_in_pass'] = None
                global_attack.save_global_config(config)
                print(ui.font("\n Logged out.", color="green"))
                time.sleep(1)
                
            elif choice == "0":
                break
            else:
                print(ui.font(" Invalid Option.", color="red"))
                time.sleep(1)
