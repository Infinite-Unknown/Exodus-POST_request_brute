# ================= Imports ================= #
import os
import sys
import time

# ================= Effects ================= #

def font(text,color=None,bold=False,dim=False,italic=False,underline=False,blink=False,inverse=False,hidden=False,strike=False):
    codes = [["bold", "1"],["dim", "2"],["italic", "3"],["underline", "4"],["blink", "5"],["inverse", "7"],["hidden", "8"],["strike", "9"],
             ["grey", "90"],["red", "91"],["green", "92"],["yellow", "93"],["blue", "94"],["magenta", "95"],["cyan", "96"],["white", "97"]]
    names = [c[0] for c in codes] 
    values = [c[1] for c in codes]

    styles = []
    for flag, name in [(bold, "bold"),(dim, "dim"),(italic, "italic"),(underline, "underline"),(blink, "blink"),
                       (inverse, "inverse"),(hidden, "hidden"),(strike, "strike")]:
        if flag and name in names:
            styles.append(values[names.index(name)])
    if color and color in names:
        styles.append(values[names.index(color)])
    if not styles:
        return text
    return f"\033[{';'.join(styles)}m{text}\033[0m"

def enter_effect(text_lines, delay=0.01, symbol="█"):
    """Entrance effect: reveal text left → right, preserves previous screen content"""
    lines = text_lines[:]
    width = max(len(line) for line in lines)

    # Reserve space
    for _ in lines:
        print()

    for x in range(width + 1):
        sys.stdout.write(f"\033[{len(lines)}F")  # move up N lines
        for line in lines:
            left = line[:x]
            middle = symbol if x < len(line) else ""
            right = " " * (len(line) - x - 1) if x < len(line) else ""
            sys.stdout.write(f"\r{left + middle + right}\033[K\n")
        sys.stdout.flush()
        time.sleep(delay)

    # Final fully revealed
    sys.stdout.write(f"\033[{len(lines)}F")
    for line in lines:
        sys.stdout.write(f"\r{line}\033[K\n")
    sys.stdout.flush()

def clear_effect(text_lines, delay=0.01, symbol="█"):
    """Exit effect: erase text left → right, preserves previous screen content"""
    lines = text_lines[:]
    width = max(len(line) for line in lines)

    for _ in lines:
        print()

    for x in range(width + 1):
        sys.stdout.write(f"\033[{len(lines)}F")
        for line in lines:
            left = " " * x
            middle = symbol if x < len(line) else " "
            right = line[x+1:] if x < len(line) else ""
            sys.stdout.write(f"\r{left + middle + right}\033[K\n")
        sys.stdout.flush()
        time.sleep(delay)

    # Fully erase at the end
    sys.stdout.write(f"\033[{len(lines)}F")
    for _ in lines:
        sys.stdout.write("\r\033[K\n")
    sys.stdout.flush()

def clear():
    """Full-screen clear"""
    os.system("cls" if os.name == "nt" else "clear")

def bg():
    clear()
    enter_effect(license, delay=0.01, symbol="│")
    print(font("\n ", color="green", inverse=True) + " Script running.")

def bg_end():
    clear()
    clear_effect(license, delay=0.01, symbol="│")
    print(font("\n ", color="red", inverse=True) + " Script ended.")
    clear()

# ================= Assets ================= #

license = [" ∞ | Infinite was here ",
           "⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⣠⠾⡄⠀",
           "⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡆⠀⠀⠀ ⠀⠀⣠⡞⠁⠀⣧⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠖⠋ ⣽⣀⣤⣤⣄⡴⠊⡹⢻⠀⠀⢸⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⣶⡶⠚⠉⠀⠀⠈⠁⢀⣩⢼⠟⠀⠀⢁⡼⠀⠀⢸⠀⠀⠀ ",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠋⠰⠋⠀⠀⠀⠀⠀⣠⠔⠋⢠⠏⠀⠀⣠⣾⠁⠀⠀⡏⠀⣠⠀ ",
           "⠀⠀⠀⠀⠀⠀⠀⠀⢀⣸⡇⠀⠀⠀⠀⠀⣠⡴⠋⠀⠀⣠⠏⠀⠀⢠⡿⠋⠀⢀⣠⠗⠋⢈⡆ ",
           "⠀⠀⠀⠀⠀⠀⠀⣴⠋⠙⠳⡄⠀⠀⠀⠾⠉⠀⠀⢀⣴⣏⠀⠀⢠⠹⣇⣤⡾⠋⠠⣾⡇⢸⡇ ",
           "⠀⠀⠀⠀⠀⠀⣀⣴⣿⣦⡀⠀⠙⢦⡀⠀⠀⠀⢀⣠⡼⠟⠁⠀⣀⡼⠋⣡⠋⠀⠀⣠⡏⠀⡜⠀",
           "⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣄⠀⠀⠳⡄⠀⠀⠀⢀⣀⣠⡶⠿⡇⣤⡾⠁⠀⠀⡾⠟⠀⣰⠃⠀",
           "⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣧⡀⣀⣹⣦⣶⣊⠉⠀⢀⠄⢠⠿⠋⠀⠀⢠⣼⠛⠀⡴⠃⠀⠀",
           "⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⢀⠏⠀⢀⡤⠖⠋⠀⣠⠞⠁⠀⠀⠀",
           "⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣤⠏⠀⠀⠀⠀⢀⣠⢾⠇⠀⠀⠀⠀⠀",
           "⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠶⣶⣤⣤⠼⠟⠁⣸⡇⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠉⠛⠿⠿⠿⠛⠛⠛⠛⠻⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⣰⡟⠁⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣇⡈⠉⠁⠀⢀⡀⠀⠀⠀⠀⠀⠀⠈⠻⠿⣯⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡤⠞⠋⠁⠀⠀⠀⠸⡌⠙⠢⣄⠀⠀⠀⣠⠴⢊⣿⡇⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⢤⡀⠀⠀⠀⠀⠀⠙⢦⡀⠘⣄⣤⣾⣿⣴⣿⠋⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣝⡒⠂⠀⠀⠀⠀⢱⣾⠟⠉⡟⠁⠸⠾⠀⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⠀⠀⠀⠀⣿⠪⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
           "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠈⠙⠒⠊⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"]
