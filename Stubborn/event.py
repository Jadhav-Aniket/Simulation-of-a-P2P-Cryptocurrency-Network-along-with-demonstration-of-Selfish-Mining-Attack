# Import necessary libraries
import random
import hashlib

# Define the Event class


class Event:
    # Constructor for Event class
    def __init__(self, Simulator, generator, fromid, toid, msg, eventtype, currenttime, Id):
        # Initialize instance variables
        self.simulator = Simulator  # A reference to the simulator object
        # A reference to the transaction or block generator that created this event
        self.generator = generator
        self.FromId = fromid  # The ID of the peer that generated the event
        self.Toid = toid  # The ID of the peer that is the intended recipient of the event
        # The type of the event, either 'Tx' (for transaction) or 'Blk' (for block)
        self.Type = eventtype
        self.Data = msg  # The data associated with the event, either a transaction or a block
        self.CurrentTime = currenttime  # The current time in the simulation
        self.ExecuteTime = 0  # The time at which the event should be executed
        self.DataId = Id  # A unique ID for the data associated with the event

    # Method to create a new event and return its properties
    def CreateEvent(self):
        # Determine if sending peer is slow and if receiving peer is slow
        for i in self.simulator.peerslist:
            if i.pid == self.FromId:
                frompeerisslow = i.is_slow
            elif i.pid == self.Toid:
                topeerspeed = i.is_slow

        # Calculate bandwidth based on whether one or both peers are slow
        if (frompeerisslow == True) and (topeerspeed == True):
            Cij = 100e6
        else:
            Cij = 5e6

        # Calculate the time it takes for data to be transmitted
        Dij = random.expovariate(96e3 / Cij)

        # Calculate the time it takes for the message to be transmitted
        if (self.Type == 'Tx'):
            msgdelay = (1000*8)/Cij
        else:
            msgdelay = (1e6*8)/Cij

        # Calculate the total delay before the event should be executed
        delay = self.simulator.rho + msgdelay + Dij

        # Set the execution time for the event
        self.ExecuteTime = self.CurrentTime + delay

        # Return a tuple representing the event with its properties
        return ((self.ExecuteTime, self.FromId, self.Toid, self.generator, self.Type, self.Data, self.DataId))
