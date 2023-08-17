import random
import hashlib
import time
import json

from peerop import Peer
from random import randrange

# Define a class called initialize_parameters


class initialize_parameters:
    # Define the constructor method for the class, which takes in a path to a file as an argument
    def __init__(self, path):
        # Open the file at the given path
        file = open(path, "r")
        # Initialize an empty list called parameter_list
        parameter_list = []
        for line in file:
            # If the first character in the line is not a "#" character
            if line[0] != "#":
                # Split the line into a list of strings.
                parameter_list.append(line.split())
        # Initialize an empty list called EventQue
        self.EventQue = []
        # Set the value of rho to a random float between 10 and 500
        self.rho = random.uniform(10, 500)
        # Set the value of Nodes to be the integer value of the first element in the first list of parameter_list
        self.Nodes = int(parameter_list[0][0])
        # Set the value of Z0 to be the integer value of the second element in the first list of parameter_list
        self.Z0 = int(parameter_list[0][1])
        # Set the value of Z1 to be the integer value of the third element in the first list of parameter_list
        self.Z1 = int(parameter_list[0][2])
        # Set the value of TerminationTime to be the integer value of the fourth element in the first list of parameter_list
        self.TerminationTime = int(parameter_list[0][3])
        # Set the value of Tmean
        self.Tmean = [float(x) for x in parameter_list[1]]
        # Set the value of Kmean
        self.Kmean = [float(x) for x in parameter_list[2]]
        # Set SlowNodesList
        self.SlowNodesList = self.setnodes(self.Z0)
        # Set LowCPUNodesList
        self.LowCPUNodesList = self.setnodes(self.Z1)
        # Set the value of HashingpowerSlow
        self.HashingpowerSlow = self.FindOutPower()
        self.peerIds = []
        # Set the value of peerslist
        self.peerslist = self.setpeers()
        # Set the value of graph
        self.graph = self.creategraph()
        # Sort the nodes in the graph in ascending order
        self.sortgraph()
        # Set the value of GenesisBlock
        self.GenesisBlock = self.CreateGenesisBlock()
        # Initialize an empty list called Que
        self.Que = []
        # Extend Que with the result of calling the initializeQue method
        self.Que.extend(self.initializeQue())
        # Indicate that the constructor method has finished executing
        pass

    def FindOutPower(self):
        power = 1/((10*self.Nodes) - (9*len(self.LowCPUNodesList)))
        return power

    def sortgraph(self):
        for i in self.graph:
            i.sort()

    def setnodes(self, var):
        #calculate number of nodes from percentage.
        TotalReqNodes = int(var * (self.Nodes)/100)
        return random.sample(range(self.Nodes), TotalReqNodes)

    def setpeers(self):
        #list of all peers
        peers = []
        isslow = False
        islowcpu = False
        #loop through total number of peers
        for i in range(self.Nodes):
            if i in self.SlowNodesList:
                isslow = True
            if i in self.LowCPUNodesList:
                islowcpu = True
            #calculate hash of peers
            peer_id = hashlib.sha256(str(i).encode()).hexdigest()
            self.peerIds.append(peer_id)
            #create objects to peers and initializeall peers with required values.
            peers.append(Peer(peer_id, isslow, islowcpu, self.Tmean[i], self.Kmean[i], self.HashingpowerSlow))
        return peers

    def CreateGenesisBlock(self):
        transcations = []
        # Add all initial balances as transactions in genesis block
        for i in self.peerslist:
            transcations.append((i.pid, i.balance))
        # Define Genesis Block Structure
        genesis_block_data = {
            'index': 0,
            'timestamp': 0,
            'generator': 'Root',
            'transactions': transcations,
            'previous_hash': '0',
        }
        # calculate Hash of Genesis Block
        genesis_block_hash = hashlib.sha256(json.dumps(
            genesis_block_data, sort_keys=True).encode()).hexdigest()
        # create genesis block as dict where hash is key and block data is value
        genesis_block = {genesis_block_hash: genesis_block_data}
        # initilize all peers blockchain with genesisblock and update topblockhash with genesis block hash.
        for i in self.peerslist:
            i.BlockTree[genesis_block_hash] = (genesis_block_data, 'Root', 0)
            i.TopBlockHash = genesis_block_hash
        # return genesis block to store
        return genesis_block

    # Define a function called creategraph that takes self as its argument
    def creategraph(self):
        # Create a list called graph that contains empty lists for each node in the graph
        graph = [[] for _ in range(self.Nodes)]

        # Loop through each node in the graph
        for currentNodeindex in range(self.Nodes):
            # Generate a random number of edges for this node between 4 and 8
            num_edges = random.randint(4, 8)

            # Create a list of all the nodes in the graph except for the current node
            vertexlist = [i for i in range(self.Nodes)]
            vertexlist.remove(currentNodeindex)

            # Count the number of edges that already exist for this node
            count = 0
            for i in graph[currentNodeindex]:
                if i in vertexlist:
                    vertexlist.remove(i)
                    count += 1

            # Subtract the count from the desired number of edges to get the number of additional edges to add
            num_edges = num_edges - count

            # If the desired number of edges is negative, continue to the next node
            if num_edges < 0:
                continue

            # Select a random sample of nodes from the remaining nodes in the graph
            # The size of the sample is equal to the number of additional edges to add
            list = random.sample(vertexlist, num_edges)

            # Add the selected nodes to the current node's list of neighbors, and add the current node to each neighbor's list
            for j in list:
                if j not in graph[currentNodeindex]:
                    graph[currentNodeindex].append(j)
                if currentNodeindex not in graph[j]:
                    graph[j].append(currentNodeindex)

        # Create a list of booleans to keep track of which nodes have been visited
        self.visited = [False] * len(graph)

        # Call the DFS function to visit every node in the graph starting at node 0
        self.DFS(graph, 0)

        # If any node in the graph hasn't been visited, generate a new graph and try again
        for v in self.visited:
            if not v:
                return self.creategraph()

        # If every node has been visited, return the graph
        return graph

    # Define a function called DFS that takes graph and vertex as its arguments
    def DFS(self, graph, vertex):
        # Mark the current node as visited
        self.visited[vertex] = True

        # Visit all of the neighbors of the current node
        for v in graph[vertex]:
            if not self.visited[v]:
                self.DFS(graph, v)

    # Define a function called initializeQue that takes self as its argument
    def initializeQue(self):
        # Create an empty list called q to hold the queue
        q = []
        
        # Loop through each peer in the list of peers
        for i in self.peerslist:
            # Choose a random peer to send the transaction to
            toID = i.pid
            while(toID == i.pid):
                toID = self.peerslist[randrange(self.Nodes)].pid
            
            # Generate a transaction and add it to the queue with its timestamp
            Tx,Timestamp = i.generateTx(toID)
            q.append((Timestamp, Tx))
            
            # Generate a block object and add it to the queue with its timestamp
            BxObj,Timestamp1 = i.GenerateBlkObj()
            q.append((Timestamp1, BxObj))
        
        # Return the completed queue
        return q