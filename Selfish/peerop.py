import numpy as np
import hashlib
import json
from random import randrange
from block import Block

class Peer:
    # Initialize the peer attributes with the provided arguments
    def __init__(self, pid, is_slow, is_low_cpu, Ttx, Ktx, Hashpower, ishonest, isstubborn):
        self.pid = pid
        self.ishonest = ishonest
        self.isstubborn = isstubborn
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.Ttx = Ttx
        self.Ktx = Ktx
        self.HashPower = Hashpower  #Initialize hashpower
        self.lastTxtime = 0  #time when previous transaction generated
        self.lastBlktime = 0 #time when previous block generated
        self.balance = randrange(200) #initial balance
        self.BlockTree = {} #Blockchain
        self.AccountStatus = {} #Maintains each account current balance.
        self.Transactions = {}  #maintains list of all transactions received
        self.LongestchainTx = [] #list of transactions which are in longest chain currently
        self.LongestChainLength = 1 #maintains length of longest chain
        self.BlocksRec = {}  #blocks received but not added to Blockchain
        self.TopBlockHash = None #hash of top block of longest chain
        self.notBroadcasted = []
        self.lead = 0 # Maintains lead of selfish miner
        self.selfishChainLength = 1 #selfish Chain length



    #Initialize longest transaction queue with genesis block transactions.
    def InitializeLongestchainTx(self,BlkId):
        self.LongestchainTx.append(self.BlockTree[BlkId]['transactions'])





    #generate transaction
    def generateTx(self,toID):
        # generate interarrival time based on exponential distribution
        interarrival = np.random.exponential(self.Ttx)
        self.lastTxtime += interarrival
        fromID = self.pid
        amount = randrange(20) # random from 0 to 200, to create some invalid transactions randomnly. 
        #generate msg of transaction
        msg = fromID + "pays" + toID + str(amount) + "coins"
        #generate hash of transaction
        TxID = hashlib.sha256(str(msg).encode()).hexdigest()
        data = (TxID, fromID, toID, amount)
        Tx = "< Tx %s : From = %s To = %s amount = %s >" %data
        return Tx, self.lastTxtime



    #receive event from event list and do th needful
    def ReceiveEvent(self, Event):
        DataId = Event[6]
        #check if event is block or Transaction
        if Event[4] == 'Tx':
            if DataId not in self.Transactions:
                #add to transactions list
                self.Transactions[DataId] = Event[5]
                return True, None
            else:
                return False, None    
        else:
            #Event is block
            #check if event is received before or not.
            if((DataId not in self.BlockTree) and (DataId not in self.BlocksRec)): 
                currenttime = Event[0]
                block = Event[5]
                blockhash = Event[6]
                blockdata = block[blockhash]
                prevhash = blockdata['previous_hash']
                #check of parent of current block in tree or not
                if prevhash in self.BlockTree:
                    AccountStatus = self.UpdateAccountStatus(prevhash)
                    #verify all transactions of block with parent chain
                    if(self.VerifyBx(blockdata,AccountStatus)):
                        #if block is valid add to Blockchain
                        BlockObj = self.AddBlocktoBlockTree(blockdata, blockhash, prevhash, currenttime)
                        if self.ishonest == False:
                            return False, BlockObj
                        return True, BlockObj
                    else:
                        return False
                else:
                    #if parent is not preset in tree add block to blockrec to add to tree later when parent arrives
                    self.BlocksRec[blockhash] = (blockdata, prevhash, )
                    if self.ishonest == False:
                        return False, None
                    return True, None     
            else:
                return False, None

    #verify block as verifying all transactions in block.
    def VerifyBx(self, blockdata, AccountStatus):
        #check each transaction is valid or not
        for Tx in blockdata['transactions']:
            status = self.VerifyTx(Tx,AccountStatus)
            if status == False:
                return False
        return True
    
#simulates Selfish Mining Attack
    def selfishattack(self, prevhash):
        if self.lead != 0:
            self.notBroadcasted.sort()
            blkdict = self.notBroadcasted[0][1]
            for _, blk in blkdict.items():
                parent = blk['previous_hash']
                if parent == prevhash:
                    if self.lead == 1:
                        self.lead = 0
                        _, blkdict = self.notBroadcasted.pop(0)
                        return False, [blkdict]
                    elif self.lead == 2:
                        self.lead = 0
                        _, blkdict = self.notBroadcasted.pop(0)
                        returndict = [blkdict]
                        _, blkdict = self.notBroadcasted.pop(0)
                        returndict.append(blkdict)
                        return False, returndict
                    else:
                        _, blkdict = self.notBroadcasted.pop(0)
                        self.lead = self.lead - 1
                        return False, [blkdict]

        else:
            return False, None


#simulates Stubborn Attack
    def stubbornattack(self, prevhash):
        if self.lead != 0:
            self.notBroadcasted.sort()
            blkdict = self.notBroadcasted[0][1]
            for _, blk in blkdict.items():
                parent = blk['previous_hash']
                if parent == prevhash:
                    if self.lead >= 2:
                        _, blkdict = self.notBroadcasted.pop(0)
                        self.lead = self.lead - 1
                        return False, [blkdict]
        else:
            return False, None
        


    #check if new chain is longest chain or not
    def iflongestchain(self,parent,blockhash,prevhash,currenttime):
        count = 0
        while(parent != 'Root'):
            parent = self.BlockTree[parent][1]
            count += 1
        #if new chain is longest chain, update longestchaintx list, and start mining new block
        if(count > self.LongestChainLength):
            self.LongestChainLength = count
            self.TopBlockHash = blockhash
            parent = prevhash
            #add all transactions of current chain to longest chain till root reached
            while(parent != 'Root'):
                self.LongestchainTx.append(self.BlockTree[parent][0]['transactions'])
                parent = self.BlockTree[parent][1]
            #start mining new block
            BlockObj = self.GenerateBlock(currenttime)
            return BlockObj
        else:
            return None

    #add block to blockchain
    def AddBlocktoBlockTree(self, blockdata, blockhash, prevhash, currenttime):
        #check if selfish block has to broadcast or not.
        if self.ishonest == False:
            broadcastlist = []
            res = self.selfishattack(prevhash)
            if res:                
                broadcastlist.extend(res)
        elif self.isstubborn == True:
            broadcastlist = []
            res = self.stubbornattack(prevhash)
            if res:                
                broadcastlist.extend(res)
        self.BlockTree[blockhash] = (blockdata, prevhash, currenttime)
        parent = blockhash
        #loop till parent of block(inside block rec) is in blockchain and search for child in block rec. 
        while (parent in self.BlockTree):
            flag = 1
            if len(self.BlocksRec):
                #iterate over all blocks in block rec.
                for BlockHash,blockRec in self.BlocksRec.items():
                    parent1 = blockRec[1]
                    # if parent in blockchain, pop that block and add to blockchain
                    if parent1 in self.BlockTree:
                        flag = 0
                        blockRec = self.BlocksRec.pop(BlockHash)
                        AccountStatus = self.UpdateAccountStatus(parent1)
                        #before adding check if bloc is valid or not
                        if(self.VerifyBx(blockRec[0],AccountStatus)):
                            #check if selfish block has to broadcast or not.
                            if self.ishonest == False:
                                res = self.selfishattack(prevhash)
                                if res:                
                                    broadcastlist.extend(res)
                            elif self.isstubborn == True:
                                res = self.stubbornattack(prevhash)
                                if res:                
                                    broadcastlist.extend(res)
                            self.BlockTree[BlockHash] = ( blockRec[0], blockRec[1], currenttime)
                        parent = BlockHash
                        break
                if flag == 1:
                    break
            else:
                break
        #If Honest Broadcast
        if self.ishonest == False and len(broadcastlist):
            return broadcastlist
        return self.iflongestchain(parent,blockhash,prevhash,currenttime)
        





    #Generate Initial trigger blocks to start mining at required time. 
    def GenerateBlkObj(self):
        # generate interarrival time based on exponential distribution
        interarrival = np.random.exponential(self.Ktx)
        hashpower = self.HashPower
        if self.is_low_cpu == False:
            hashpower = hashpower * 10
        #calculate time of first block to start mining from initial system timing from given Ktx value
        time = interarrival/hashpower
        self.lastBlktime += time
        fromID = self.pid
        msg = f"TriggerBlk fromID = {fromID}"
        #generate hash of trigger block
        BxID = hashlib.sha256(str(msg).encode()).hexdigest()
        data = (BxID, fromID,)
        Bx = "< Bx %s : From = %s >" %data
        return Bx, self.lastBlktime

    #verify transaction
    # if it is valid return true
    # else false
    def VerifyTx(self,Tx,AccountStatus):
        tx = Tx.split()
        fromid = tx[6]
        toid = tx[9]
        amount = float(tx[12])
        AccountStatus[fromid] -= amount
        AccountStatus[toid] += amount
        if AccountStatus[fromid] < 0:
            AccountStatus[fromid] += amount
            AccountStatus[toid] -= amount
            return False
        else:
            return True





    #Generate block// start mining a block by adding transactions
    def GenerateBlock(self, currenttime):
        BlkTx = []
        count = 0
        prevhash = self.TopBlockHash
        AccountStatus = self.UpdateAccountStatus(prevhash)
        #add transactions from all received transactions.
        for Txid,Tx in self.Transactions.items():
            #block can only have less than 1000 transactions
            if(count < 1000):
                #Transaction should not already added to longest chain
                if Tx not in self.LongestchainTx:
                    #verify required transaction
                    if self.VerifyTx(Tx,AccountStatus):
                        BlkTx.append(Tx)
                        count += 1
            else:
                break
        fromid = self.pid
        toid = 'ALL'
        #Create block obj and add to list of events by returning object.
        BlockObj = Block(prevhash, fromid, toid, BlkTx, currenttime,self.Ktx)
        Blockevent = BlockObj.createblock(self.is_low_cpu,self.HashPower)
        return Blockevent





    #check if block is valid to broadcast
    #if block is generated by self, then broadcast to all neighbours
    #If block is already broadcasted earlier, dont repeat to avoid looping.
    def IfBroadcast(self, EventEle):
        currenttime = EventEle[0]
        block = EventEle[5]
        blockhash = EventEle[6]
        blockdata = block[blockhash]
        prevhash = blockdata['previous_hash']
        #check If block is valid to mining and to get added to blockchain
        if prevhash == self.TopBlockHash:
            #Mine block
            UpdatedBlock = self.MineBlock(blockdata,currenttime)
            #As block Mined, start mining again
            BlockObj = self.GenerateBlock(currenttime)
            #If node is selfish it will not broadcast the block to others.
            if self.ishonest == False:
                self.notBroadcasted.append((currenttime, UpdatedBlock))
                self.lead = self.lead + 1
                UpdatedBlock = None
            return (UpdatedBlock,BlockObj)
        else:
            #if block failed to mine, start mining new block
            BlockObj = self.GenerateBlock(currenttime)
            return (None, BlockObj)





    #mine Block
    def MineBlock(self,block_data,currenttime):
        #create coinbase trasaction.
        fromID = "CoinBase"
        toID = self.pid
        Reward = 50
        msg = fromID + "pays" + toID + str(Reward) + "coins"
        TxID = hashlib.sha256(str(msg).encode()).hexdigest()
        data = (TxID, toID, Reward)
        CoinbaseTx = "< TxnID %s : %s mines %s coins >" %data
        
        #upadte block by adding coinbase trasaction
        new_block_data = {
            'previous_hash': block_data['previous_hash'],
            'generator': block_data['generator'],
            'timestamp': block_data['timestamp'],
            'transactions': block_data['transactions'],
            'coinbase': CoinbaseTx,
            }

        #generate hash of block
        BlockHash = hashlib.sha256(json.dumps(new_block_data).encode()).hexdigest()
        #generate block to get added to tree
        block = {BlockHash: new_block_data}
        #Add block to blockchain
        self.BlockTree[BlockHash] = (new_block_data, self.TopBlockHash, currenttime)
        self.TopBlockHash = BlockHash
        self.LongestChainLength += 1
        #upadte list of transactions present in longestchain transactions list
        self.LongestchainTx.append(new_block_data['transactions'])
        return block










    #Calculate account balances of all peers by looping through all transactions
    def UpdateAccountStatus(self, blockhash):
        parent = blockhash
        AccountStatus = {}
        #parent of current chain
        generator = self.BlockTree[parent][0]['generator']
        #loop untill Genesis block reached
        while(parent != 'Root'):
            #check if transactions are present in block, if not skip the block 
            if len(self.BlockTree[parent][0]['transactions']) < 1:
                parent = self.BlockTree[parent][1]
                continue
            Txlist = self.BlockTree[parent][0]['transactions']
            if (self.BlockTree[parent][1] == 'Root'):
                for i in Txlist:
                    if i[0] not in AccountStatus:
                        AccountStatus[i[0]] = i[1]
                    else:
                        AccountStatus[i[0]] += i[1]
                break
            else:
                for i in Txlist:
                    tx = i.split()
                    fromid = tx[6]
                    toid = tx[9]
                    amount = tx[12]
                    # update accounts with credits and debits
                    if fromid not in AccountStatus:
                        AccountStatus[fromid] = -float(amount)
                    elif toid not in AccountStatus:
                        AccountStatus[toid] = float(amount)
                    else:
                        AccountStatus[fromid] -= float(amount)
                        AccountStatus[toid] += float(amount)
                AccountStatus[generator] += 50
            #update parent to next parent
            parent = self.BlockTree[parent][1]
        """for key,amount in AccountStatus.items():
            AccountStatus[key] += 200"""
        #Return total calculated status of All Accounts.
        return AccountStatus