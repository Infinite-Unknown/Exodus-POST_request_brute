import os
import time
import json
import shutil

import ui
import menus
import attacker

LOGIN_FILE = os.path.join(os.getcwd(), 'Input', 'SavedLogins', 'fast_single.json')
REQUEST_FILE = os.path.join(os.getcwd(), 'Input', 'temp.txt')

def setup_account(is_change_cred=False):
    ui.clear()
    if is_change_cred:
        print(ui.font(" Change Credential ", color="cyan", inverse=True))
    else:
        print(ui.font(" Setup Account (Required) ", color="cyan", inverse=True))
        
    print(ui.font("\n Type 'back' anytime to cancel.", color="yellow"))
    email = input(" Enter APU Email: ").strip()
    if email.lower() == 'back':
        return False
        
    password = input(" Enter Password: ").strip()
    if password.lower() == 'back':
        return False
    
    if not email or not password:
        print(ui.font(" [!] Email and Password cannot be empty.", color="red"))
        time.sleep(1.5)
        return False
        
    login_data = {'email': email, 'password': password}
    
    print(ui.font("\n [*] Validating credentials and capturing cURL... Please wait.", color="yellow"))
    
    test_dest = os.path.join(os.getcwd(), 'Input', 'test_curl_fast.txt')
    if os.path.exists(test_dest):
        try:
            os.remove(test_dest)
        except:
            pass
            
    # Suppress output mostly by using headless=True
    menus.auto_grab_curl(save_dest=test_dest, login_data=login_data, headless=True)
    
    if os.path.exists(test_dest):
        # Validation successful! cURL was captured.
        # Move it to temp.txt (the DEFAULT location for single attack)
        try:
            shutil.move(test_dest, REQUEST_FILE)
        except Exception as e:
            # Fallback if move fails
            os.replace(test_dest, REQUEST_FILE)
            
        # Force save credentials
        os.makedirs(os.path.dirname(LOGIN_FILE), exist_ok=True)
        with open(LOGIN_FILE, 'w', encoding='utf-8') as lf:
            json.dump(login_data, lf)
            
        print(ui.font("\n [SUCCESS] Account linked and cURL saved successfully!", color="green"))
        time.sleep(1.5)
        return True
    else:
        print(ui.font("\n [!] Failed. Please check your email/password or your internet connection.", color="red"))
        time.sleep(2.5)
        return False

def check_account():
    # Force setup if missing credential file or missing the temp.txt
    if not os.path.exists(LOGIN_FILE) or not os.path.exists(REQUEST_FILE):
        success = False
        while not success:
            success = setup_account(is_change_cred=False)

def fast_menu():
    while True:
        ui.clear()
        print(ui.font("          - Exodus [Flash] -          \n", color="cyan", inverse=True))
        
        ui.enter_effect([
            "1. Attack (Multithreaded)",
            "2. Direct Send OTP [3 digits]",
            "",
            "3. Refresh Login Session",
            "4. Change Credential",
            "",
            "0. Exit"
        ], delay=0.02, symbol="█")
        
        choice = input("\nInput: ").strip()
            
        if choice == "1":
            ui.bg()
            print(ui.font(" [Press 'q' or 'esc' to stop attacking]", color="yellow"))
            attacker.start_experimental()
            ui.bg_end()
        elif choice == "2":
            ui.bg()
            attacker.test_connection()
            ui.bg_end()
        elif choice == "3":
            print(ui.font("\n [*] Refreshing login session in background...", color="cyan"))
            try:
                import subprocess
                
                # We use a subprocess to prevent async frame / playwright hanging the main thread
                script = f"""
import sys
import json
import traceback
try:
    from menus import auto_grab_curl
    with open(r'{LOGIN_FILE}', 'r') as f:
        login_data = json.load(f)
    auto_grab_curl(save_dest=r'{REQUEST_FILE}', login_data=login_data, headless=True)
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)
"""
                result = subprocess.run(["python", "-c", script], capture_output=True, text=True)
                
                if result.returncode == 0 and "ERROR:" not in result.stdout:
                    print(ui.font(" [SUCCESS] Session refreshed!", color="green"))
                else:
                    print(ui.font(f" [ERROR] Could not refresh. Details: {result.stdout.strip()} {result.stderr.strip()}", color="red"))
                    
            except Exception as e:
                print(ui.font(f" [ERROR] Subprocess failed: {e}", color="red"))
            time.sleep(1.5)
            
        elif choice == "4":
            setup_account(is_change_cred=True)
        elif choice == "0":
            ui.clear()
            print(ui.font(" ", color="cyan", inverse=True) + " Exiting Fast Single Mode.")
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

if __name__ == "__main__":
    os.system("title Exodus - Fast_Single")
    os.makedirs(os.path.join(os.getcwd(), 'Input', 'SavedLogins'), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), 'Input', 'SavedRequests'), exist_ok=True)
    
    check_account()
    fast_menu()
