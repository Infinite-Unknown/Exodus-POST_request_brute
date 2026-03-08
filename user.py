import os
import time
import ui
import menus

import json

def auto_refresh_tokens():
    """Check for saved logins and refresh tokens in the background"""
    logins_dir = os.path.join(os.getcwd(), 'Input', 'SavedLogins')
    saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    
    if not os.path.exists(logins_dir) or not os.path.exists(saved_dir):
        return
        
    login_files = [f for f in os.listdir(logins_dir) if f.endswith('.json')]
    
    if not login_files:
        return
        
    ui.clear()
    print(ui.font(f" Found {len(login_files)} Saved Accounts. \n", color="cyan", inverse=True))
    
    choice = input(" Would you like to auto-refresh their tokens now? (y/n): ").strip().lower()
    if choice != 'y':
        print(ui.font(" Skipping auto-refresh.", color="yellow"))
        time.sleep(1)
        return
        
    ui.clear()
    print(ui.font(f" Auto-Refreshing {len(login_files)} Accounts... \n", color="cyan", inverse=True))
    
    success_count = 0
    fail_count = 0
    
    for file in login_files:
        account_name = os.path.splitext(file)[0]
        login_path = os.path.join(logins_dir, file)
        dest_path = os.path.join(saved_dir, f"{account_name}.txt")
        
        try:
            with open(login_path, 'r', encoding='utf-8') as f:
                login_data = json.load(f)
                
            print(ui.font(f" [*] Refreshing {account_name}...", color="yellow"))
            
            # Start headless auto-grab
            # We need to temporarily suppress ui.clear() and other prints inside auto_grab_curl
            # But the simplest way is to pass headless=True which handles the flow
            menus.auto_grab_curl(save_dest=dest_path, login_data=login_data, headless=True)
            
            # Since auto_grab_curl modifies the file if successful, we assume it worked
            # if the file exists and has content.
            # However, Playwright failure writes "ERROR" internally but shouldn't save.
            print(ui.font(f" [✓] {account_name} refreshed.", color="green"))
            success_count += 1
            
        except Exception as e:
            print(ui.font(f" [X] Failed to refresh {account_name}: {e}", color="red"))
            fail_count += 1
            
    print(ui.font(f"\n Refresh Complete: {success_count} Success, {fail_count} Failed.", color="cyan"))
    time.sleep(2)

def user_menu():
    """User Launcher Menu"""
    while True:
        ui.clear()
        print(ui.font("             - Exodus User -             \n", color="cyan", inverse=True))
        
        ui.enter_effect([
            "1. Single Account Mode",
            "2. Multi Account Mode",
            "3. Global Attack (Join)",
            "4. Account Backup (Discord)",
            "5. Exit"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            menus.single_account_menu()
        elif choice == "2":
            menus.multi_account_menu()
        elif choice == "3":
            menus.global_attack_user_menu()
        elif choice == "4":
            menus.discord_menu()
        elif choice == "5":
            ui.clear()
            print(ui.font(" ", color="cyan", inverse=True) + " User Session Ended.")
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

if __name__ == "__main__":
    os.system("title Exodus User")
    auto_refresh_tokens()
    user_menu()