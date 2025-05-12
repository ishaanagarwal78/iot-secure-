import hashlib
import json
import time
from typing import List, Dict
import threading

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0
        self.merkle_root = self._calculate_merkle_root()
        self.hash = self.calculate_hash()

    def _calculate_merkle_root(self) -> str:
        if not self.transactions:
            return hashlib.sha256("empty".encode()).hexdigest()
        
        # Create leaf nodes from transactions
        leaves = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                 for tx in self.transactions]
        
        # Build Merkle tree
        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])  # Duplicate last element if odd number
            
            next_level = []
            for i in range(0, len(leaves), 2):
                combined = leaves[i] + leaves[i+1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            leaves = next_level
            
        return leaves[0] if leaves else hashlib.sha256("empty".encode()).hexdigest()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Dict] = []
        self.lock = threading.Lock()
        
        # Create genesis block
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        genesis_block = Block(0, [], time.time(), "0")
        self.mine_block(genesis_block)
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, sender: str, recipient: str, data: Dict) -> bool:
        with self.lock:
            transaction = {
                "sender": sender,
                "recipient": recipient,
                "timestamp": time.time(),
                "data": data
            }
            self.pending_transactions.append(transaction)
            return True

    def mine_block(self, block: Block) -> bool:
        target = "0" * self.difficulty
        
        while block.hash[:self.difficulty] != target:
            block.nonce += 1
            block.hash = block.calculate_hash()
        return True

    def create_block(self) -> None:
        with self.lock:
            if not self.pending_transactions:
                return None
                
            new_block = Block(
                len(self.chain),
                self.pending_transactions[:],
                time.time(),
                self.get_latest_block().hash
            )
            
            self.pending_transactions = []
            self.mine_block(new_block)
            self.chain.append(new_block)
            return new_block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

            if current_block.merkle_root != current_block._calculate_merkle_root():
                return False

        return True

    def get_chain_data(self) -> List[Dict]:
        return [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "transactions": block.transactions,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root
            }
            for block in self.chain
        ] 