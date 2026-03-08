import os
import time
import json
import shutil
import subprocess

import ui
import menus
import attacker

def broadcast_otp():
    saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    if not os.path.exists(saved_dir):
        print(ui.font(" No accounts found.", color="red"))
        time.sleep(1)
        return
        
    files = [f for f in os.listdir(saved_dir) if f.endswith(".txt")]
    if not files:
        print(ui.font(" No accounts found.", color="red"))
        time.sleep(1)
        return
        
    print(ui.font("\n Direct Send OTP [Broadcast]", color="cyan", inverse=True))
    otp = input("\n Enter OTP to send to all accounts (3 digits) [or 'back']: ").strip()
    if otp.lower() == 'back':
        return
        
    if not otp: otp = "000"
        
    ui.bg()
    print(ui.font(f"\n Broadcasting OTP {otp} to {len(files)} accounts...", color="yellow", inverse=True))
    for f in files:
        file_path = os.path.join(saved_dir, f)
        url, headers = attacker.load_config_from_file(file_path)
        if not url or not headers:
            print(ui.font(f" [SKIP] {f} - Invalid config", color="red"))
            continue
            
        print(f" -> Sending for {os.path.splitext(f)[0]}...")
        resp, err = attacker.check_otp(otp, url=url, headers=headers)
        if err:
            print(ui.font(f"    [ERROR] {err}", color="red"))
        elif resp and 'data' in resp and resp['data'] and resp['data'].get('updateAttendance'):
            print(ui.font(f"    [SUCCESS] Valid!", color="green"))
        elif resp and 'errors' in resp:
            err_msg = resp['errors'][0]['message']
            if "You are not registered to this class" in err_msg:
                 print(ui.font(f"    [FAILED] Not Result", color="yellow"))
            else:
                 print(ui.font(f"    [FAILED] {err_msg}", color="red"))
        else:
            print(ui.font(f"    [FAILED] Unknown response", color="red"))
            
    ui.bg_end()
    input("\n Press Enter to return to menu...")

def refresh_all_sessions():
    saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
    
    if not os.path.exists(logins_dir) or not os.path.exists(saved_dir):
        print(ui.font("\n [!] No accounts to refresh.", color="red"))
        time.sleep(1.5)
        return
        
    login_files = [f for f in os.listdir(logins_dir) if f.endswith(".json") and f != "fast_single.json"]
    
    if not login_files:
        print(ui.font("\n [!] No saved login credentials found for multi-accounts.", color="red"))
        time.sleep(1.5)
        return
        
    print(ui.font(f"\n [*] Refreshing sessions for {len(login_files)} target(s)...", color="cyan"))
    
    for lf in login_files:
        acc_name = os.path.splitext(lf)[0]
        login_path = os.path.join(logins_dir, lf)
        req_path = os.path.join(saved_dir, f"{acc_name}.txt")
        
        print(ui.font(f"\n -> Refreshing {acc_name}...", color="yellow"))
        
        script = f"""
import sys
import json
import traceback
try:
    from menus import auto_grab_curl
    with open(r'{login_path}', 'r', encoding='utf-8') as f:
        login_data = json.load(f)
    auto_grab_curl(save_dest=r'{req_path}', login_data=login_data, headless=True)
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)
"""
        result = subprocess.run(["python", "-c", script], capture_output=True, text=True)
        
        if result.returncode == 0 and "ERROR:" not in result.stdout:
            print(ui.font(f"    [SUCCESS] {acc_name} refreshed!", color="green"))
        else:
            print(ui.font(f"    [ERROR] {acc_name} failed. Details: {result.stdout.strip()} {result.stderr.strip()}", color="red"))
            
    print(ui.font("\n [DONE] Refresh complete.", color="cyan", inverse=True))
    input("\n Press Enter to return to menu...")

def manage_accounts_menu():
    saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    if not os.path.exists(saved_dir):
        os.makedirs(saved_dir)
        
    while True:
        ui.clear()
        print(ui.font(" Manage Accounts [Blitz] ", color="magenta", inverse=True))
        
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
                        
                    login_file = os.path.join(logins_dir, f"{os.path.splitext(dest_name)[0]}.json")
                    try:
                        with open(login_file, 'w', encoding='utf-8') as f:
                            json.dump(login_data, f)
                        print(ui.font(f" [SUCCESS] Login details saved for {os.path.splitext(dest_name)[0]}.", color="green"))
                    except Exception as e:
                        print(ui.font(f" [ERROR] Could not save login details: {e}", color="red"))
                else:
                    print(ui.font(" [!] Missing email or password. Proceeding with manual login.", color="yellow"))
                    
            from menus import auto_grab_curl
            auto_grab_curl(save_dest=dest_path, login_data=login_data)
                
        elif sub_choice == "2":
            import tkinter as tk
            from tkinter import filedialog
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
                        
                        # Also rename the json if it exists
                        logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
                        old_json = os.path.join(logins_dir, f"{os.path.splitext(old_name)[0]}.json")
                        new_json = os.path.join(logins_dir, f"{os.path.splitext(new_name)[0]}.json")
                        if os.path.exists(old_json):
                            os.rename(old_json, new_json)
                            
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
                        
                        # Also attempt to delete associated JSON
                        logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
                        login_file = os.path.join(logins_dir, f"{os.path.splitext(target)[0]}.json")
                        if os.path.exists(login_file):
                            os.remove(login_file)
                            
                    except Exception as e:
                        print(ui.font(f" [ERROR] Failed to delete {target}: {e}", color="red"))
                print(ui.font(f" [SUCCESS] Deleted {deleted_count} account(s) and their saved credentials (if any).", color="green"))
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

def blitz_menu():
    while True:
        ui.clear()
        print(ui.font("          - Exodus [Blitz] -          \n", color="cyan", inverse=True))
        
        # Show account count
        saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
        files = [f for f in os.listdir(saved_dir) if f.endswith(".txt")] if os.path.exists(saved_dir) else []
        print(ui.font(f" Accounts Loaded: {len(files)}", color="white"))
        
        ui.enter_effect([
            "1. Attack (Multi-Account)",
            "2. Direct Send OTP [Broadcast]",
            "",
            "3. Refresh All Login Sessions",
            "4. Manage Accounts",
            "",
            "0. Exit"
        ], delay=0.02, symbol="█")
        
        choice = input("\nInput: ").strip()
        
        if choice == "1":
            if not files:
                print(ui.font(" No accounts loaded.", color="red"))
                time.sleep(1)
                continue
                
            ui.clear()
            print(ui.font(" Select Accounts for Attack ", color="cyan", inverse=True))
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
                selected_files = files
            elif select_choice == "s":
                print(ui.font("\n Enter account numbers separated by commas (e.g., 1,3,4):", color="yellow"))
                print(ui.font(" Or enter a range (e.g., 1-5):", color="yellow"))
                selection = input(" Selection: ").strip()
                
                selected_indices = set()
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
            
            ui.clear()
            print(ui.font(" Selected Accounts ", color="green", inverse=True))
            print(f"\n Attacking with {len(selected_files)} account(s):\n")
            for f in selected_files:
                print(f"  • {os.path.splitext(f)[0]}")
            
            confirm = input("\n Proceed? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
                
            ui.bg()
            print(ui.font(" [Press 'q' or 'esc' to stop attacking]", color="yellow"))
            attacker.run_multi_account_attack(selected_files)
            ui.bg_end()
            
        elif choice == "2":
            broadcast_otp()
            
        elif choice == "3":
            refresh_all_sessions()
            
        elif choice == "4":
            manage_accounts_menu()
            
        elif choice == "0":
            ui.clear()
            print(ui.font(" ", color="cyan", inverse=True) + " Exiting Blitz Mode.")
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

if __name__ == "__main__":
    os.system("title Exodus - Blitz_Multi")
    os.makedirs(os.path.join(os.getcwd(), 'Input', 'SavedLogins'), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), 'Input', 'SavedRequests'), exist_ok=True)
    
    blitz_menu()
