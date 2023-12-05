__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2023"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
import numpy as np

class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):

        #TODO: DEFINE YOUR ATTRIBUTES HERE
        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        env_conf = self.network.receive()
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        cell_val = env_conf["cell_val"] #value of the cell the agent is located in

        self.network.send({"header" : ATTRIBUTION})
        env_conf = self.network.receive()
        self.ymin, self.ymax = env_conf["attribution"]
        
        Thread(target=self.msg_cb, daemon=True).start()

    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            print(msg)

            if msg["header"]==MOVE:
                self.x=msg["x"]
                self.y=msg["y"] 
            
    
    #TODO: CREATE YOUR METHODS HERE...
        
    def move_random(self):
        """move randomly in map
        """
        move = np.random.randint(1,9)
        cmd = {"header" : MOVE, "direction": move}
        self.network.send(cmd)

    def move_to_bounds(self):
        """agent moves to the place it has been attributed.
        """
        print("Actual Y used ---> ", self.y)
        if self.y <= self.ymin : 
            print("going up, ymin = ", self.ymin)
            cmd = {"header" : MOVE, "direction": DOWN}
            
        elif self.y >= self.ymax : 
            print("going down, ymax = ", self.ymax)
            cmd = {"header" : MOVE, "direction": UP}
        else : 
            options = [8,7,3]
            random_index = np.random.randint(0,3)
            cmd = {"header" : MOVE, "direction": RIGHT}
            print("i'm in place, moving forward :", options[random_index])
        self.network.send(cmd)
    def move_to(self, x, y):
        while (self.x != x) or (self.y != y):
            dx = self.x - x
            dy = self.y - y

            if dy < 0: dir = DOWN
            if dy > 0: dir = UP
            if dx < 0: dir = RIGHT
            if dx > 0: dir = LEFT
            if dy < 0 and dx < 0: dir = DOWN_RIGHT
            if dy > 0 and dx > 0: dir = UP_LEFT
            if dy > 0 and dx < 0: dir = UP_RIGHT
            if dy < 0 and dx > 0: dir = DOWN_LEFT
            cmds = {"header": 2,
                    "direction": dir}
            self.network.send(cmds)
            time.sleep(0.5)

if __name__ == "__main__":
    from random import randint
    import time
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    """try:    #Manual control test
        while True:
            cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            agent.network.send(cmds)"""
    try:    #Automatic control
        print("Hi, i'm an agent : ", agent.agent_id)
        
        while True:
            agent.move_to_bounds()
            time.sleep(1)
            

    except KeyboardInterrupt:
        pass




