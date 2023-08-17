import hashlib
import numpy as np
import json

class Block:
    def __init__(self, prevhash, fromid, toid, Txlist, currenttime, Ktx ):
        # Initialize the block attributes with the provided arguments
        self.Prevhash = prevhash
        self.FromId = fromid
        self.generator = fromid # The generator of the block is the same as the fromid
        self.Toid = toid
        self.Tx = Txlist
        self.CurrentTime = currenttime
        self.ExecuteTime = 0
        self.Ktx = Ktx
        self.block = None
        self.BlockId = None
        self.Type = None

    def createblock(self, islowcpu, hashpower,):
        # Generate a new block with the provided parameters
        interarrival = np.random.exponential(self.Ktx)
        if islowcpu == False:
            hashpower = hashpower * 10
        time = interarrival/hashpower
        self.ExecuteTime = self.CurrentTime + time
        self.Type = 'BlkObj'
        # Construct a dictionary with the block data
        block_data = {
            'previous_hash': self.Prevhash,
            'generator': self.generator,
            'timestamp': self.ExecuteTime,
            'transactions': self.Tx,
            'coinbase': None,
            }
        # Calculate the hash of the block using SHA256
        BlockHash = hashlib.sha256(json.dumps(block_data).encode()).hexdigest()
        # Construct a dictionary with the block and its hash
        self.block = {BlockHash: block_data}
        # Return a tuple with information about the new block
        return ((self.ExecuteTime, self.FromId, self.Toid, self.generator, self.Type, self.block, BlockHash))
