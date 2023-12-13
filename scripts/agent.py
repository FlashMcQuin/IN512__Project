__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2023"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *
import time
from threading import Thread
import numpy as np

class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):

        #TODO: DEFINE YOUR ATTRIBUTES HERE
        self.value_log=[0]
        self.key_position = False
        self.box_position = False
        self.key_discovered = False
        self.box_discovered = False
        self.completed = False
        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        env_conf = self.network.receive()
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        #self.history.append([self.x, self.y])
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        self.cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        self.network.send({"header" : ATTRIBUTION})
        env_conf = self.network.receive()
        self.ymin, self.ymax = env_conf["attribution"]
        Thread(target=self.msg_cb, daemon=True).start()



    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            print("Message from : ", msg["sender"], " : ", msg)
            if msg["header"]==MOVE:
                self.x=msg["x"]
                self.y=msg["y"] 
                self.cell_val=msg["cell_val"]
            if msg["header"] == GET_DATA:
                self.cell_val = msg["cell_val"]
            if msg["header"] == 0 : 
                if msg["Msg type"] == 1 and msg["owner"] == self.agent_id:
                    self.key_position = msg["position"]
                    print("La position de ma clé est : ", msg["position"])
                elif msg["Msg type"] == 2 and msg["owner"] == self.agent_id : 
                    self.box_position = msg["position"]
                    print("La position de ma box est : ", msg["position"])
            if msg["header"] == 5 and msg["owner"] == self.agent_id:
                if msg["type"] == 0 : 
                    self.key_position = self.get_position()
                    self.key_discovered = True
                    print("J'ai récupéré ma clé")
                if msg["type"] == 1 : 
                    self.box_position = self.get_position()
                    self.box_discovered = True
                    print("J'ai récupéré ma box")
    

    #TODO: CREATE YOUR METHODS HERE...
    def update_position(self, int_move) : 
        self.x += self.move[int_move][0]
        self.y += self.move[int_move][1]
    
    def get_position(self):
        return [self.x, self.y]
    
    def move_random(self):
        """move randomly in map
        """
        move = np.random.randint(1,9)
        cmd = {"header" : MOVE, "direction": move}
        self.network.send(cmd)

    def move_to_bounds_old(self):
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

    def move_to_bounds_center(self):
        ymoy = int((self.ymin+self.ymax)/2)
        self.move_to(1, ymoy-1)
        print("I'm in place")

    def move_to(self, x, y):
        while (self.x != x) or (self.y != y):
            self.scan_cell()
            dx = self.x - x
            dy = self.y - y
            if dy < 0: dir = DOWN
            elif dy > 0: dir = UP
            if dx < 0: dir = RIGHT
            elif dx > 0: dir = LEFT
            if dy < 0 and dx < 0: dir = DOWN_RIGHT
            if dy > 0 and dx > 0: dir = UP_LEFT
            if dy > 0 and dx < 0: dir = UP_RIGHT
            if dy < 0 and dx > 0: dir = DOWN_LEFT
            cmds = {"header": 2,
                    "direction": dir}
            self.network.send(cmds)
            time.sleep(1)

    def zigzag(self):
        self.move_to(self.x+2, self.y+2)
        time.sleep(1)
        self.move_to(self.x+2, self.y-2)

    def scan_cell(self):
        print(f"scanning cell : ({self.x},{self.y}) -> value : {self.cell_val}")
        if self.cell_val>0:
            match self.cell_val : 
                case 0.25 : 
                    print("close to a key")
                case 0.3 : 
                    print("close to a box")
                case 0.5:
                    print("I am verty close to a key")
                    self.value_log.append(self.cell_val) #keep this last value in memory
                case 0.6:
                    print("I close to a box")
                    self.value_log.append(self.cell_val)
            #By remembering if the value was à.6 or 0.5, we know wether we are on a key or a box.
            if self.cell_val == 1.0 and self.value_log[-1] == 0.6:
                print("I'm on a Box !!")
                self.network.send({"header": BROADCAST_MSG, 
                                   "msg type": BOX_DISCOVERED, 
                                   "position":(self.x, self.y),
                                   "owner":None})

            elif self.cell_val == 1.0 and self.value_log[-1] == 0.5:
                print("I'm on a Key !!")
                self.network.send({"header": BROADCAST_MSG,
                                    "msg type": KEY_DISCOVERED,
                                    "position":(self.x, self.y),
                                    "owner":None})
        else : 
            print("nothing to declare")
            print(self.cell_val)

        return self.cell_val

if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    """
    try:    #Manual control test
        while True:
            cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
                agent.update_position(cmds["direction"])
                #agent.history.append(agent.get_position())
            agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
    """
    try:    #Automatic control
        print("Hi, i'm an agent : ", agent.agent_id)
        agent.move_to_bounds_center()
        while True:
            agent.zigzag()
            time.sleep(1)
            

    except KeyboardInterrupt:
        pass

"""
COMMANDS on AGENT
0 <-> Broadcast msg
1 <-> Get data
2 <-> Move
3 <-> Get nb connected agents
4 <-> Get nb agents
5 <-> Get item owner

DIRECTIONS : 
0 <-> Stand
1 <-> Left
2 <-> Right
3 <-> Up
4 <-> Down
5 <-> UL
6 <-> UR
7 <-> DL
8 <-> DR
"""



