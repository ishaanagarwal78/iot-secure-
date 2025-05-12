import threading
from client.main import IoTDevice
import time
import sys
import random
from datetime import datetime
import requests
from config import SERVER_URL

def check_server_availability():
    """Check if the server is available"""
    try:
        response = requests.get(f"{SERVER_URL}/api/chain")
        return response.status_code == 200
    except requests.RequestException:
        return False

def generate_realistic_data(device_id: str) -> dict:
    """Generate more realistic sensor data"""
    current_time = datetime.now().isoformat()
    
    # Simulate different data patterns for different devices
    base_temp = 25 + (hash(device_id) % 5)  # Different base temperature for each device
    base_humidity = 50 + (hash(device_id) % 10)  # Different base humidity for each device
    
    return {
        "device_info": {
            "id": device_id,
            "type": "environmental_sensor",
            "location": "test_location",
            "timestamp": current_time
        },
        "sensor_data": {
            "temperature": round(base_temp + random.uniform(-2, 2), 2),  # °C
            "humidity": round(base_humidity + random.uniform(-5, 5), 2),  # %
            "pressure": round(1013.25 + random.uniform(-10, 10), 2),  # hPa
            "air_quality": round(random.uniform(0, 100), 1),  # AQI
            "light_level": round(random.uniform(0, 1000), 1),  # lux
        },
        "status": {
            "battery_level": round(random.uniform(60, 100), 1),  # %
            "signal_strength": round(random.uniform(-90, -30), 1),  # dBm
            "error_count": 0
        }
    }

def run_device(device_id: str):
    """Run a single IoT device instance"""
    print(f"[Device {device_id}] Starting up...")
    print(f"[Device {device_id}] Attempting to connect to server at {SERVER_URL}")
    
    # Wait for server to be available
    while not check_server_availability():
        print(f"[Device {device_id}] Server not available, retrying in 5 seconds...")
        time.sleep(5)
    
    device = IoTDevice(device_id)
    retries = 0
    max_retries = 3
    
    # Registration with retry logic
    while retries < max_retries:
        print(f"[Device {device_id}] Attempting registration (attempt {retries + 1}/{max_retries})...")
        try:
            if device.register():
                print(f"[Device {device_id}] ✓ Registered successfully")
                break
            print(f"[Device {device_id}] ✗ Registration failed, server rejected registration")
        except Exception as e:
            print(f"[Device {device_id}] ✗ Registration error: {str(e)}")
        retries += 1
        if retries < max_retries:
            time.sleep(2)
    else:
        print(f"[Device {device_id}] ✗ Failed to register after {max_retries} attempts")
        return

    # Main device loop
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    while True:
        try:
            # Authentication check
            if not device.is_authenticated:
                print(f"[Device {device_id}] Authenticating...")
                if not device.authenticate():
                    print(f"[Device {device_id}] ✗ Authentication failed, retrying in 5 seconds...")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"[Device {device_id}] ✗ Too many consecutive failures, restarting device...")
                        return
                    time.sleep(5)
                    continue
                print(f"[Device {device_id}] ✓ Authentication successful")
                consecutive_failures = 0

            # Generate and send data
            data = generate_realistic_data(device_id)
            print(f"[Device {device_id}] Sending data: {data}")
            
            if device.submit_data(data):
                print(f"[Device {device_id}] ✓ Data submitted successfully")
                consecutive_failures = 0
            else:
                print(f"[Device {device_id}] ✗ Failed to submit data")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"[Device {device_id}] ✗ Too many consecutive failures, restarting device...")
                    return
                device.is_authenticated = False

            time.sleep(3)  # Send data every 3 seconds

        except Exception as e:
            print(f"[Device {device_id}] ✗ Error: {str(e)}")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"[Device {device_id}] ✗ Too many consecutive failures, restarting device...")
                return
            time.sleep(5)

def main():
    print(f"Starting test devices... Server URL: {SERVER_URL}")
    
    # Wait for server to be available
    while not check_server_availability():
        print("Waiting for server to become available...")
        time.sleep(5)
    
    print("Server is available, starting devices...")
    
    # Number of simulated devices
    num_devices = 3
    
    while True:
        # Create and start device threads
        threads = []
        for i in range(num_devices):
            device_id = f"test_sensor_{i+1}"
            thread = threading.Thread(target=run_device, args=(device_id,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            time.sleep(1)  # Stagger device starts
        
        try:
            # Keep the main thread running and show periodic status
            while True:
                alive_threads = sum(1 for t in threads if t.is_alive())
                print("\n=== Test Devices Status ===")
                print(f"Active devices: {alive_threads}/{num_devices}")
                print("Press Ctrl+C to stop all devices")
                print("==========================\n")
                
                if alive_threads < num_devices:
                    print("Some devices have stopped, restarting...")
                    break
                    
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\nStopping all devices...")
            sys.exit(0)
            
        print("Restarting all devices in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main() 