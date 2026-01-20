import os
import time
import tkinter as tk
from tkinter import filedialog
import ui
import attacker

# ================= Setup ================= #
os.system("title Exodus.exe")

def main_menu():
    while True:
        ui.clear()
        print(ui.font("                - Exodus -                \n", color="white", inverse=True))
        
        # Enter effect for menu items
        ui.enter_effect([
            "1. Start Bruteforce", 
            "2. Test Connection", 
            "3. Experimental: Multi-Threaded Bruteforce",
            "4. Experimental: Multiple Account Attack",
            "5. Configure Main Attack Request (cURL) [Bash]",
            "6. Add/Manage Multiple cURL Requests",
            "7. Exit"
        ], delay=0.05, symbol="█")
        choice = input("\nInput: ")

        if choice == "1":
            ui.bg()
            attacker.start()
            ui.bg_end()
        elif choice == "2":
            ui.bg()
            attacker.test_connection()
            ui.bg_end()
        elif choice == "3":
            ui.bg()
            attacker.start_experimental()
            ui.bg_end()
        elif choice == "4":
            ui.bg()
            attacker.run_multi_account_attack()
            ui.bg_end()
        elif choice == "5":
            ui.clear()
            print(ui.font(" Configuration Menu ", color="yellow", inverse=True))
            
            input_dir = os.path.join(os.getcwd(), 'Input')
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)
                
            file_path = os.path.join(input_dir, 'temp.txt')
            
            if os.path.exists(file_path):
                print(f"\n [INFO] Configuration file found at: {file_path}")
                print(ui.font(" 1. Edit/Overwrite existing cURL string", color="cyan"))
                print(ui.font(" 2. Go back", color="white"))
                sub_choice = input("\n Input: ")
                if sub_choice != "1":
                    continue
            else:
                 print(f"\n [INFO] No configuration found. Please select a file containing your cURL command.")

            print(ui.font("\n Press Enter to browse for your cURL text file...", color="green"))
            input()
            
            # Tkinter File Dialog
            root = tk.Tk()
            root.withdraw() # Hide main window
            root.attributes('-topmost', True) # Bring to front
            
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
            while True:
                ui.clear()
                print(ui.font(" Manage Saved Requests ", color="magenta", inverse=True))
                
                saved_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
                if not os.path.exists(saved_dir):
                    os.makedirs(saved_dir)
                    
                files = [f for f in os.listdir(saved_dir) if f.endswith(".txt")]
                
                print(f"\n Current Requests ({len(files)}):")
                if not files:
                    print("  (None)")
                else:
                    for i, f in enumerate(files):
                        print(f"  {i+1}. {f}")
                        
                print("\n" + "-"*30)
                print(" 1. Add New Request (Import File)")
                print(" 2. Rename Request")
                print(" 3. Delete Request")
                print(" 4. Back to Main Menu")
                
                sub_choice = input("\n Input: ")
                
                if sub_choice == "1":
                    print(ui.font("\n Press Enter to browse for request file...", color="green"))
                    input()
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_selected = filedialog.askopenfilename(title="Select cURL Text File")
                    if file_selected:
                        # Ask for name
                        dest_name = input(" Enter name for this account (e.g. Account1): ").strip()
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
                            print(ui.font(f"\n [SUCCESS] Saved as {dest_name}", color="green"))
                        except Exception as e:
                            print(ui.font(f" [ERROR] {e}", color="red"))
                        time.sleep(1.5)
                        
                elif sub_choice == "2":
                    if not files:
                        print(ui.font(" No files to rename.", color="yellow"))
                        time.sleep(1)
                        continue
                    try:
                        idx = int(input(" Enter number to rename: ")) - 1
                        if 0 <= idx < len(files):
                            old_name = files[idx]
                            new_name = input(f" Rename '{old_name}' to (no extension needed): ").strip()
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
                        print(ui.font(" No files to delete.", color="yellow"))
                        time.sleep(1)
                        continue
                    try:
                        idx = int(input(" Enter number to delete: ")) - 1
                        if 0 <= idx < len(files):
                            target = files[idx]
                            confirm = input(f" Are you sure you want to delete '{target}'? (y/n): ").lower()
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
            
        elif choice == "7":
            ui.clear()
            print(ui.font(" ", color="red", inverse=True) + " Exit Successful.")
            break
        else:
             print(ui.font(" Invalid Option. Please key in 1-7", color="red"))
             time.sleep(1)

if __name__ == "__main__":
    main_menu()
