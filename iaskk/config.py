"""
Configuration settings for the IoT Security Framework
"""

# Server Configuration
SERVER_HOST = "127.0.0.1"  # Listen on localhost for testing
SERVER_PORT = 5000
SERVER_DEBUG = True

# Security Configuration
ECC_CURVE = 'secp256k1'
HASH_ALGORITHM = 'sha256'
BLOCK_SIZE = 10  # Number of transactions per block

# IoT Client Configuration
IOT_DATA_INTERVAL = 5  # seconds between data transmissions
SERVER_URL = "http://127.0.0.1:5000"  # Local testing URL

# Blockchain Configuration
DIFFICULTY = 4  # Number of leading zeros required for proof of work
MAX_TRANSACTIONS_PER_BLOCK = 10

# Database Configuration (using SQLite for simplicity)
DATABASE_URL = "sqlite:///blockchain.db" 