import os
import time
import ui
import menus

def admin_menu():
    """Admin Launcher Menu"""
    while True:
        ui.clear()
        print(ui.font("             - Exodus Admin -             \n", color="red", inverse=True))
        
        ui.enter_effect([
            "1. Global Attack Controller",
            "2. Exit"
        ], delay=0.02, symbol="█")
        choice = input("\nInput: ")
        
        if choice == "1":
            menus.global_attack_admin_menu()
        elif choice == "2":
            ui.clear()
            print(ui.font(" ", color="red", inverse=True) + " Admin Session Ended.")
            break
        else:
            print(ui.font(" Invalid Option.", color="red"))
            time.sleep(1)

if __name__ == "__main__":
    os.system("title Exodus Admin")
    admin_menu()
