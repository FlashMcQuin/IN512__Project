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
            
            if msg["header"] == BROADCAST_MSG : 
                if msg["msg type"] == KEY_DISCOVERED and msg["owner"] == self.agent_id:
                    self.key_position = msg["position"]
                    print("La position de ma clé est : ", msg["position"])
                elif msg["msg type"] == BOX_DISCOVERED and msg["owner"] == self.agent_id : 
                    self.box_position = msg["position"]
                    print("La position de ma box est : ", msg["position"])

            if msg["header"] == GET_ITEM_OWNER and msg["owner"] == self.agent_id:
                if msg["type"] == KEY_TYPE :
                    self.key_position = (self.x, self.y)
                    self.key_discovered = True
                    print("J'ai récupéré ma clé")
                elif msg["type"] == BOX_TYPE : 
                    self.box_position = (self.x, self.y)
                    self.box_discovered = True
                    print("J'ai récupéré ma box")
            elif msg["header"] == GET_ITEM_OWNER and msg["owner"] != self.agent_id:
                if msg["owner"] is None : 
                    print("You fool")
                else :
                    if msg["type"] == KEY_TYPE :
                        discovered = KEY_DISCOVERED
                    elif msg["type"] == BOX_TYPE :
                        discovered = BOX_DISCOVERED
                    self.network.send({"header": BROADCAST_MSG, 
                                        "msg type": discovered, 
                                        "position":(self.x, self.y),
                                        "owner": msg["owner"]})
            # TODO : On peut créer une action qui ajoute quel objet de quel agent a été trouvé à un dictionnaire
            # -> permet monitorer où chacun en est, quand tout le monde connait la position de ses objets, 
            #       on arrête de chercher 
    
    #TODO: CREATE YOUR METHODS HERE...
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
        if self.y<self.ymax :
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
                case 1.0 :
                    self.network.send({"header" : GET_ITEM_OWNER})

        else : 
            print(".")

        return self.cell_val
    def game_state(self):
        print(f"Position clé : {self.key_position}, position box : {self.box_position} \n clé decouverte :{self.key_discovered}, box décoverte : {self.box_discovered}, complété : {self.completed}")
    
    def check_walls(self, up_direction, down_direction):
        """checks for walls, if there is, changes the direction of the zigzags
        """
        if self.x == self.w-1: 
            print("wall !")
            return UP_LEFT, DOWN_LEFT
        elif self.x == 0 : 
            print("wall !")
            return UP_RIGHT, DOWN_RIGHT
        else :
            return up_direction, down_direction
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()
    agent = Agent(args.server_ip)
    try:    #Automatic control
        print("Hi, i'm an agent : ", agent.agent_id)
        agent.move_to_bounds_center()
        UP_LR, DOWN_LR = UP_RIGHT, DOWN_RIGHT #start by going right
        while True:
            while agent.y < agent.ymax-1 : 
                UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR)
                cmds = {"header": MOVE,"direction": DOWN_LR}
                agent.network.send(cmds)
                agent.scan_cell()
                time.sleep(1)
            while agent.y >= agent.ymin+1 :
                UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR)
                cmds = {"header": MOVE,"direction": UP_LR}
                agent.network.send(cmds)
                agent.scan_cell()
                time.sleep(1)

            time.sleep(1)
            agent.game_state()
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



