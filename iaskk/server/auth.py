from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature
import base64
import json
from typing import Dict, Optional
import os

class DeviceAuthenticator:
    def __init__(self):
        self.registered_devices: Dict[str, bytes] = {}
        
    def register_device(self, device_id: str, public_key_bytes: bytes) -> bool:
        """Register a new device with its public key"""
        if device_id in self.registered_devices:
            return False
        
        self.registered_devices[device_id] = public_key_bytes
        return True
    
    def verify_signature(self, device_id: str, message: str, signature: bytes) -> bool:
        """Verify a message signature from a device"""
        if device_id not in self.registered_devices:
            return False
            
        try:
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256K1(),
                self.registered_devices[device_id]
            )
            
            public_key.verify(
                signature,
                message.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    def get_device_public_key(self, device_id: str) -> Optional[bytes]:
        """Get the public key for a registered device"""
        return self.registered_devices.get(device_id)

class AuthenticationMessage:
    @staticmethod
    def create_challenge() -> str:
        """Create a random challenge for device authentication"""
        # Generate a random 32-byte challenge
        random_bytes = os.urandom(32)
        return base64.b64encode(random_bytes).decode()
    
    @staticmethod
    def verify_challenge_response(authenticator: DeviceAuthenticator,
                                device_id: str,
                                challenge: str,
                                signature: bytes) -> bool:
        """Verify a device's response to an authentication challenge"""
        return authenticator.verify_signature(device_id, challenge, signature) 