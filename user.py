import os
import time
import ui
import menus

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
    user_menu()