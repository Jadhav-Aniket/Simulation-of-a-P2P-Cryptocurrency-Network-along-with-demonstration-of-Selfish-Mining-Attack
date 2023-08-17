from random import randrange
from graphviz import Digraph

from initialize import initialize_parameters
from event import Event



def CreateNewTx(IndexOfNode):
    # Generate a new transaction to a random node in the network
    toID = simulator.peerslist[IndexOfNode].pid
    # loop until toid is same as fromid
    while(toID == simulator.peerslist[IndexOfNode].pid):
        toID = simulator.peerslist[randrange(simulator.Nodes)].pid
    Tx,Timestamp = simulator.peerslist[IndexOfNode].generateTx(toID)
    # Add the new transaction to the simulation queue
    simulator.Que.append((Timestamp, Tx))


def popQue():
    # Get the next element from the simulation queue
    Ele = simulator.Que.pop(0)
    # Parse the element
    tokens = Ele[1].split()
    currenttime = Ele[0]
    msg = Ele[1]
    eventtype = tokens[1]
    EleId = tokens[2]
    generator = tokens[6]
    IndexOfNode = simulator.peerIds.index(generator)
    if eventtype == 'Bx':
        # If the element is a "Bx" event, generate a new block
        Eventele = simulator.peerslist[IndexOfNode].GenerateBlock(currenttime)
        # Add the new block to the simulation event queue
        simulator.EventQue.append(Eventele)
    else:
        # If the element is not a "Bx" event, create a new transaction and send it to all peers
        fromid = tokens[6]
        CreateNewTx(IndexOfNode) #create New Transaction
        for i in simulator.graph[IndexOfNode]:
            toid = simulator.peerIds[i]
            # Create an event object for each peer in the network and add it to the simulation event queue
            EventObj = Event(simulator, generator, fromid, toid, msg, eventtype, currenttime, EleId)
            simulator.EventQue.append(EventObj.CreateEvent())
    return currenttime








def popEvent():
    # Retrieve the first event in the queue and extract various pieces of information from it
    EventEle = simulator.EventQue.pop(0)
    currenttime = EventEle[0]
    FromId = EventEle[1]
    ToId = EventEle[2]
    generator = EventEle[3]
    DataId = EventEle[6]
    # Determine the index of the sender in the list of peer IDs
    IndexOfFromId = simulator.peerIds.index(FromId)
    # If the receiver is "ALL", broadcast the data to all peers in the network and create new events for each recipient
    if ToId == 'ALL':
        # Ask the sender's peer object to broadcast the data and return any updated blocks
        UpdatedBlock,BlockObj = simulator.peerslist[IndexOfFromId].IfBroadcast(EventEle)
        # Append any new blocks to the event queue
        simulator.EventQue.append(BlockObj)
        # If any blocks were updated, create new events for each recipient of the data
        if UpdatedBlock:
            for blockhash,blockdata in UpdatedBlock.items():
                eventtype = 'Block'
                # For each neighbor of the sender, create a new event to transmit the data
                for i in simulator.graph[IndexOfFromId]:
                    toid = simulator.peerIds[i]
                    EventObj = Event(simulator, generator, FromId, toid, UpdatedBlock, eventtype, currenttime, blockhash)
                    simulator.EventQue.append(EventObj.CreateEvent())
            # Return the current time
            return currenttime
        else:
            # If no blocks were updated, return the current time
            return currenttime
    else:
        # If the receiver is not "ALL", check if the recipient has received the data
        if FromId == generator :
            # If the sender is the generator, update the sender's peer object to reflect that the data has been transmitted
            IndexOfFromId = simulator.peerIds.index(generator)
            Result = simulator.peerslist[IndexOfFromId].ReceiveEvent(EventEle)
        # Determine the index of the recipient in the list of peer IDs
        IndexOfToId = simulator.peerIds.index(ToId)
        # Update the recipient's peer object to reflect that the data has been transmitted
        Result, BlockObj = simulator.peerslist[IndexOfToId].ReceiveEvent(EventEle)
        # Append any new blocks to the event queue
        if BlockObj:
            simulator.EventQue.append(BlockObj)  
        # If the recipient received the data, create new events for each recipient of the data
        if (Result is True):
            for i in simulator.graph[IndexOfToId]:
                if i != IndexOfFromId:
                    NewfromId = simulator.peerIds[IndexOfToId]
                    NewToId = simulator.peerIds[i]
                    EventObj = Event(simulator, generator, NewfromId, NewToId, EventEle[5], EventEle[4], currenttime, DataId)
                    simulator.EventQue.append(EventObj.CreateEvent())    
        # Return the current time
        return currenttime




def visualize():
    # Loop through each peer in the network
    for i in simulator.peerslist:
        # Create a dictionary to store the block tree for the peer as a graph
        graphdict = {'Root' : []}
        # Add each block in the block tree to the graph dictionary
        for key,block in i.BlockTree.items():
            graphdict[key] = []
        # Add the children of each block to the graph dictionary
        for key,block in i.BlockTree.items():
            graphdict[block[1]].append(key)
        # Create a new dictionary to store the graph using integer keys
        listofkeys = list(graphdict.keys())
        newgraphdict = {}
        for lk in listofkeys:
            if(len(graphdict[lk])>0):
                if lk not in newgraphdict:
                    newgraphdict[str(listofkeys.index(lk))] = []
                for child in graphdict[lk]:
                    newgraphdict[str(listofkeys.index(lk))].append(str(listofkeys.index(child)))
        # Create a new directed graph using the graphviz package
        dot = Digraph()
        # Loop through each node in the graph dictionary and add it to the directed graph
        dot.attr(rankdir='LR',splines='line')
        for parent, children in newgraphdict.items():
            dot.node(parent)
            for child in children:
                dot.node(child)
                dot.edge(parent, child)
        # Render the graph as an image file and save it in the 'results' directory
        dot.render(str(simulator.peerslist.index(i))+ "node",'results/')
        # Write the timings for each block to a file in the 'timings' directory
        with open("timings/" +  str(simulator.peerslist.index(i))+".txt", 'w') as f:
            for key,block in i.BlockTree.items():
                f.write(str(key) +str("\t") + str(block[2]) + "\n")


def findratio():
     # Calculate and print the ratio
    # Loop through each peer in the network
    for i in simulator.peerslist:
        totalblocks = 0
        longestchaintotalblocks = 0
        peerid = i.pid
        parent = i.TopBlockHash
        #calculate blocks in longest chain by current peer
        while(parent != 'Root'):
                generatorofblock = i.BlockTree[parent][0]['generator']
                if peerid == generatorofblock:
                    longestchaintotalblocks += 1
                parent = i.BlockTree[parent][1]
        #calculate total blocks in blockchain by current peer 
        for hash,block in i.BlockTree.items():
            generatorofblock = block[0]['generator']
            if peerid == generatorofblock:
                    totalblocks += 1
        print()
        #print(f"{longestchaintotalblocks} {totalblocks}")
        if totalblocks == 0:
            continue
        print(f"Ratio of (block in longest chain by peer/total block by peer) {simulator.peerIds.index(peerid)}:  {longestchaintotalblocks/totalblocks}")










if __name__ == "__main__":
    # Initialize simulator with parameters from input file
    simulator = initialize_parameters('input.txt')
    # Set initial time and counter
    GlobalTime = 0
    i = 0
    # Run the simulation until termination time is reached
    while GlobalTime < simulator.TerminationTime:
        # Sort the Que and EventQue lists
        simulator.Que.sort()
        simulator.EventQue.sort()
        # Print current iteration and global time
        print(i,GlobalTime)
        # Check if both Que and EventQue have elements
        if(len(simulator.Que) and len(simulator.EventQue)):
            # Compare the time of the earliest events in Que and EventQue
            simulatorQuetime = simulator.Que[0][0]
            EventQuetime = simulator.EventQue[0][0]
            # Pop the earliest event and update global time
            if(simulatorQuetime < EventQuetime):
                if(simulatorQuetime <= simulator.TerminationTime):
                    GlobalTime = popQue()
                else:
                    break
            else:
                if(EventQuetime <= simulator.TerminationTime):
                    GlobalTime = popEvent()
                else:
                    break
        # Check if only Que has elements
        elif(len(simulator.Que)):
            simulatorQuetime = simulator.Que[0][0]
            # Pop the earliest event and update global time
            if(simulatorQuetime <= simulator.TerminationTime):
                GlobalTime = popQue()
            else:
                break
        # Check if only EventQue has elements
        elif(len(simulator.EventQue)):
            EventQuetime = simulator.EventQue[0][0]
            # Pop the earliest event and update global time
            if(EventQuetime <= simulator.TerminationTime):
                GlobalTime = popEvent()
            else:
                break
        # Exit the loop if both Que and EventQue are empty
        else:
            break
        # Increment the counter
        i += 1
    # Print final global time and visualize the simulation
    print()
    print(GlobalTime)
    visualize()
    findratio()
    exit(0)
