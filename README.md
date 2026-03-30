# Exodus

A Python-powered tool for brute-forcing APSpace Attendix OTPs (One-Time Passwords). Supports single-account, multi-account, and collaborative global attacks via Discord integration.

> **Press `Q` / `ESC` at any time to emergency-stop all running processes.**

---

## Downloads

| Edition | Description | Download |
|---------|-------------|----------|
| **Exodus Flash** | Quick single-account mode | [Exodus (Flash).exe](https://github.com/Infinite-Unknown/Exodus-POST_request_brute/raw/refs/heads/main/dist/Exodus%20(Flash).exe) |
| **Exodus Blitz** | Quick multi-account mode | [Exodus (Blitz).exe](https://github.com/Infinite-Unknown/Exodus-POST_request_brute/raw/refs/heads/main/dist/Exodus%20(Blitz).exe) |
| **Exodus User** | Global Attack – join as participant | [ExodusUser.exe](https://github.com/Infinite-Unknown/Exodus-POST_request_brute/raw/refs/heads/main/dist/ExodusUser.exe) |
| **Exodus Admin** | Global Attack – admin controller | [ExodusAdmin.exe](https://github.com/Infinite-Unknown/Exodus-POST_request_brute/raw/refs/heads/main/dist/ExodusAdmin.exe) |
| **Exodus** | Fallback For Others Failed | [Exodus.exe](https://github.com/Infinite-Unknown/Exodus-POST_request_brute/raw/refs/heads/main/dist/Exodus.exe) |

> [!NOTE]
> The `Exodus (Flash).exe` and `Exodus (Blitz).exe` are the latest edition with simplified everything.
> If want more control or extra stuff setup in a conda environment `admin.py` then `user.py`.
> `Exodus.exe` is the oldest stable build for fallback if others failed.

---

## Editions Overview

### Exodus (Full)
The all-in-one launcher containing every feature:
- **Single Account Mode** – attack with one APSpace session.
- **Multi Account Mode** – attack with multiple accounts simultaneously.
- **Global Attack (Admin / User)** – collaborative attacks synced through Discord.
- **Discord Webhook Backup** – back up your account configs to a Discord channel.

### Exodus Flash
Streamlined single-account edition. Automatically prompts for APU credentials on first run, captures the session via headless browser, and jumps straight to the attack menu.

**Menu options:** Multi-threaded Attack · Direct Send OTP · Refresh Session · Change Credential

### Exodus Blitz
Streamlined multi-account edition. Manage and attack with multiple accounts at once, with auto-login and session refresh for all stored accounts.

**Menu options:** Broadcast Attack (all accounts) · Manage Accounts · Refresh All Sessions

### Exodus User
Lightweight client for **Global Attack** mode. Register/login to a shared Discord-backed database, bind your cURL config, and participate in coordinated group attacks started by an admin.

Also includes **Sentinel Mode** – an experimental attendance monitor that watches your APSpace attendance page for changes and can auto-launch an attack when new attendance opens.

### Exodus Admin
Admin console for **Global Attack** mode. Set up a Discord bot & webhooks, manage registered users and classes, initiate attacks for all opted-in users, and monitor a live status dashboard.

---

## Setup Tutorial & Usage

**Video walkthrough:** [APSPACE_BRUTE_TUTORIAL (YouTube)](https://youtu.be/P1tsijMZ_v0)

### Quick Start (Recommended – Flash / Blitz / User)
1. Download the desired `.exe` from the table above.
2. Run the executable – it will create an `Input/` folder alongside it automatically.
3. Enter your **APU email** and **password** when prompted.
4. The app will open a headless browser, log in, and capture the session cURL automatically.
5. Once captured, you're ready to attack!

### Manual cURL Setup (Full Edition)
If you prefer to import a cURL manually:

1. **Trigger a failed OTP request:**
   - Go to the APSpace Attendix Update page.
   - Enter a wrong OTP (e.g. `000`) so the "Failed" notification pops up.

2. **Capture the request:**
   - Open DevTools (`Ctrl + Shift + I`) → **Network** tab.
   - Find the `POST` request to `graphql` corresponding to the failed OTP.

3. **Copy as cURL:**
   - Right-click the request → **Copy** → **Copy as cURL (bash)**.

4. **Import into Exodus:**
   - Paste the cURL into a `.txt` file and save it.
   - Run `Exodus.exe`, go to **Single Account Mode** → **Setup cURL (Import File)**.
   - Browse and select your text file.

### Auto-Grab cURL (Full / Multi Edition)
Instead of manual cURL capture, use **Setup cURL (Auto-Grab)**:
- A Playwright-automated browser opens, you log in, submit any OTP, and the cURL is captured automatically.
- Supports both manual and fully-automated (headless) login with saved credentials.

### Sentinel Mode (User Edition)
An experimental attendance monitor:
1. Select a saved account or enter credentials.
2. Set a refresh interval (default 60s) and optionally enable auto-attack.
3. The app logs into APSpace, opens the Attendance page, and watches for changes.
4. When attendance data changes (new class, percentage shift, etc.), it alerts you with a system beep.
5. If auto-attack is enabled, it automatically captures a fresh session and launches the brute-force attack.

---

## Features

| Feature | Full | Flash | Blitz | User | Admin |
|---------|:----:|:-----:|:-----:|:----:|:-----:|
| Single-account attack | ✅ | ✅ | — | — | — |
| Multi-threaded brute-force | ✅ | ✅ | ✅ | — | — |
| Multi-account attack | ✅ | — | ✅ | — | — |
| Auto cURL capture (Playwright) | ✅ | ✅ | ✅ | — | — |
| Auto session refresh | ✅ | ✅ | ✅ | — | — |
| Credential storage | ✅ | ✅ | ✅ | — | — |
| Global Attack (user) | ✅ | — | — | ✅ | — |
| Global Attack (admin) | ✅ | — | — | — | ✅ |
| Sentinel Mode (attendance monitor) | — | — | — | ✅ | — |
| Discord webhook backup | ✅ | — | — | — | — |
| Live status dashboard | — | — | — | — | ✅ |
| Discord command control (!start/!stop) | — | — | — | — | ✅ |

---

## Architecture

```
Exodus/
├── menus.py          # Main menu system & Playwright auto-grab cURL
├── attacker.py       # OTP brute-force engine (single, multi, global)
├── flash.py          # Flash edition entry point (single-account)
├── blitz.py          # Blitz edition entry point (multi-account)
├── user.py           # User edition entry point (global attack participant)
├── admin.py          # Admin edition entry point (global attack controller)
├── global_attack.py  # Discord-backed collaborative attack module
├── discord_db.py     # Discord webhook database for account backup
├── ui.py             # Terminal UI effects (colors, animations)
├── Assets/
│   └── icon.png      # Application icon
├── Input/            # Runtime data (gitignored)
│   ├── temp.txt            # Active single-account cURL config
│   ├── SavedRequests/      # Multi-account cURL configs (*.txt)
│   ├── SavedLogins/        # Stored credentials (*.json)
│   ├── discord_config.json # Discord webhook config
│   └── global_config.json  # Global attack config
└── dist/             # Pre-built Windows executables
```

---

## Requirements (for running from source)

```
pip install -r requirements.txt
playwright install chromium
```

**Dependencies:** `requests`, `keyboard`, `playwright`

---

## Disclaimer

This tool is for **educational purposes only**. Unauthorized use against systems you do not own or have permission to test is illegal.

I will not take any responsibility for any form of abuse or account bans.
