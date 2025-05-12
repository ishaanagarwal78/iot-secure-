from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import threading
import time
from blockchain import Blockchain
from auth import DeviceAuthenticator, AuthenticationMessage
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_HOST, SERVER_PORT, DIFFICULTY

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for testing
blockchain = Blockchain(difficulty=DIFFICULTY)
authenticator = DeviceAuthenticator()

# Store active challenges
active_challenges = {}

print("Server starting up - Device registration state cleared")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register_device():
    data = request.get_json()
    device_id = data.get('device_id')
    public_key = data.get('public_key')
    
    if not device_id or not public_key:
        return jsonify({'error': 'Missing device_id or public_key'}), 400
        
    try:
        public_key_bytes = bytes.fromhex(public_key)
        if authenticator.register_device(device_id, public_key_bytes):
            return jsonify({'status': 'success', 'message': 'Device registered successfully'})
        else:
            return jsonify({'error': 'Device already registered'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid public key format'}), 400

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Missing device_id'}), 400
        
    if device_id not in authenticator.registered_devices:
        return jsonify({'error': 'Device not registered'}), 401
        
    challenge = AuthenticationMessage.create_challenge()
    active_challenges[device_id] = challenge
    
    return jsonify({
        'status': 'success',
        'challenge': challenge
    })

@app.route('/api/verify', methods=['POST'])
def verify_authentication():
    data = request.get_json()
    device_id = data.get('device_id')
    signature = data.get('signature')
    
    if not device_id or not signature:
        return jsonify({'error': 'Missing required fields'}), 400
        
    challenge = active_challenges.get(device_id)
    if not challenge:
        return jsonify({'error': 'No active challenge found'}), 400
        
    try:
        signature_bytes = bytes.fromhex(signature)
        if AuthenticationMessage.verify_challenge_response(
            authenticator, device_id, challenge, signature_bytes
        ):
            del active_challenges[device_id]
            return jsonify({'status': 'success', 'message': 'Authentication successful'})
        else:
            return jsonify({'error': 'Invalid signature'}), 401
    except ValueError:
        return jsonify({'error': 'Invalid signature format'}), 400

@app.route('/api/submit-data', methods=['POST'])
def submit_data():
    data = request.get_json()
    device_id = data.get('device_id')
    sensor_data = data.get('data')
    signature = data.get('signature')
    
    if not all([device_id, sensor_data, signature]):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        signature_bytes = bytes.fromhex(signature)
        message = json.dumps(sensor_data, sort_keys=True)
        
        if authenticator.verify_signature(device_id, message, signature_bytes):
            blockchain.add_transaction(device_id, "network", sensor_data)
            socketio.emit('new_data', {
                'device_id': device_id,
                'data': sensor_data,
                'timestamp': time.time()
            })
            return jsonify({'status': 'success', 'message': 'Data submitted successfully'})
        else:
            return jsonify({'error': 'Invalid signature'}), 401
    except ValueError:
        return jsonify({'error': 'Invalid data format'}), 400

@app.route('/api/chain')
def get_chain():
    return jsonify({
        'chain': blockchain.get_chain_data(),
        'length': len(blockchain.chain)
    })

def block_mining_thread():
    while True:
        blockchain.create_block()
        socketio.emit('new_block', {
            'chain': blockchain.get_chain_data(),
            'length': len(blockchain.chain)
        })
        time.sleep(10)  # Create a new block every 10 seconds if there are transactions

if __name__ == '__main__':
    # Start the block mining thread
    mining_thread = threading.Thread(target=block_mining_thread)
    mining_thread.daemon = True
    mining_thread.start()
    
    # Start the Flask application
    socketio.run(app, host=SERVER_HOST, port=SERVER_PORT, debug=True) 