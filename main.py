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
            "4. Configure Request (cURL)",
            "5. Exit"
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
            
        elif choice == "5":
            ui.clear()
            print(ui.font(" ", color="red", inverse=True) + " Exit Successful.")
            break
        else:
             print(ui.font(" Invalid Option. Please key in 1, 2, 3, 4 or 5", color="red"))
             time.sleep(1)

if __name__ == "__main__":
    main_menu()
