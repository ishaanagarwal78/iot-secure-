import json
import time
import requests
import random
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_URL, IOT_DATA_INTERVAL

class IoTDevice:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.private_key = ec.generate_private_key(ec.SECP256K1())
        self.public_key = self.private_key.public_key()
        self.server_url = SERVER_URL
        self.is_authenticated = False
        print(f"Initialized device {device_id} with server URL: {SERVER_URL}")

    def get_public_key_bytes(self) -> bytes:
        """Get the public key in raw point format"""
        return self.public_key.public_bytes(
            encoding=Encoding.X962,
            format=PublicFormat.UncompressedPoint
        )

    def sign_message(self, message: str) -> bytes:
        return self.private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )

    def register(self) -> bool:
        """Register the device with the server"""
        try:
            print(f"Attempting to register with server at {self.server_url}")
            response = requests.post(
                f"{self.server_url}/api/register",
                json={
                    "device_id": self.device_id,
                    "public_key": self.get_public_key_bytes().hex()
                },
                timeout=10  # Add timeout
            )
            if response.status_code == 200:
                print("Registration successful")
                return True
            else:
                print(f"Registration failed with status {response.status_code}: {response.text}")
                return False
        except requests.RequestException as e:
            print(f"Registration failed due to connection error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return False

    def authenticate(self) -> bool:
        """Authenticate with the server"""
        try:
            # Request challenge
            print("Requesting authentication challenge...")
            response = requests.post(
                f"{self.server_url}/api/authenticate",
                json={"device_id": self.device_id},
                timeout=10
            )
            
            if response.status_code == 401 and "Device not registered" in response.text:
                print("Device not registered, attempting re-registration...")
                if self.register():
                    print("Re-registration successful, retrying authentication...")
                    return self.authenticate()
                return False
                
            if response.status_code != 200:
                print(f"Failed to get challenge: {response.text}")
                return False
                
            challenge = response.json()["challenge"]
            print("Received challenge, signing response...")
            
            # Sign challenge
            signature = self.sign_message(challenge)
            
            # Verify signature with server
            print("Sending signed challenge...")
            verify_response = requests.post(
                f"{self.server_url}/api/verify",
                json={
                    "device_id": self.device_id,
                    "signature": signature.hex()
                },
                timeout=10
            )
            
            self.is_authenticated = verify_response.status_code == 200
            if self.is_authenticated:
                print("Authentication successful")
            else:
                print(f"Authentication failed: {verify_response.text}")
            return self.is_authenticated
            
        except requests.RequestException as e:
            print(f"Authentication failed due to connection error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during authentication: {e}")
            return False

    def generate_sensor_data(self) -> dict:
        """Generate simulated sensor data"""
        return {
            "temperature": round(random.uniform(20, 30), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "pressure": round(random.uniform(980, 1020), 2),
            "timestamp": time.time()
        }

    def submit_data(self, data: dict) -> bool:
        """Submit sensor data to the server"""
        if not self.is_authenticated:
            print("Device not authenticated")
            return False
            
        try:
            # Ensure data is properly formatted
            if not isinstance(data, dict):
                print("Invalid data format: must be a dictionary")
                return False

            message = json.dumps(data, sort_keys=True)
            signature = self.sign_message(message)
            
            print("Sending data to server...")
            response = requests.post(
                f"{self.server_url}/api/submit-data",
                json={
                    "device_id": self.device_id,
                    "data": data,
                    "signature": signature.hex()
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Failed to submit data: {response.text}")
                return False
                
            print("Data submitted successfully")
            return True
            
        except requests.RequestException as e:
            print(f"Data submission failed due to connection error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during data submission: {e}")
            return False

def main():
    device = IoTDevice("raspberry_pi_01")
    
    print("Registering device...")
    if not device.register():
        print("Failed to register device")
        return
        
    print("Device registered successfully")
    
    while True:
        if not device.is_authenticated:
            print("Authenticating...")
            if not device.authenticate():
                print("Authentication failed, retrying in 5 seconds...")
                time.sleep(5)
                continue
            print("Authentication successful")
        
        data = device.generate_sensor_data()
        print(f"Sending data: {data}")
        
        if device.submit_data(data):
            print("Data submitted successfully")
        else:
            print("Failed to submit data")
            device.is_authenticated = False  # Force re-authentication
            
        time.sleep(IOT_DATA_INTERVAL)

if __name__ == "__main__":
    main() 