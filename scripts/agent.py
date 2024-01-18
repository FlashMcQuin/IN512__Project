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
        self.nb_agents = 99
        self.key_position = None
        self.box_position = None
        self.searching = True

        self.key_discovered = False
        self.box_discovered = False
        self.completed = False

        self.found_items = []
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
            #print("Message from : ", msg["sender"], " : ", msg)
            if msg["header"]==MOVE: # Update position and cell value
                self.x=msg["x"]
                self.y=msg["y"]
                self.cell_val=msg["cell_val"]

            if msg["header"] == BROADCAST_MSG : # Handle a broadcast message
                if msg["msg type"] == KEY_DISCOVERED and msg["owner"] == self.agent_id: # My key has been found
                    self.key_position = msg["position"]
                    print(f"Agent {msg['sender']+1} found my key at : {msg['position']}")
                elif msg["msg type"] == BOX_DISCOVERED and msg["owner"] == self.agent_id : # My box has been found
                    self.box_position = msg["position"]
                    print(f"Agent {msg['sender']+1} found my box at : {msg['position']}")
                self.found_items.append(msg["position"])
                print(f"found items: {len(self.found_items)}")

            # If the broadcast message says it found the item of the concerned agent
            if msg["header"] == GET_ITEM_OWNER and msg["owner"] == self.agent_id:
                if msg["type"] == KEY_TYPE :
                    self.key_position = (self.x, self.y)
                    self.key_discovered = True
                    discovered = KEY_DISCOVERED
                    print("J'ai récupéré ma clé")
                elif msg["type"] == BOX_TYPE : 
                    self.box_position = (self.x, self.y)
                    self.box_discovered = True
                    discovered = BOX_DISCOVERED
                    print("J'ai récupéré ma box")
                self.found_items.append((self.x, self.y))
                # Warn others I have found one of my items.
                self.network.send({"header": BROADCAST_MSG, 
                                        "msg type": discovered, 
                                        "position":(self.x, self.y),
                                        "owner": self.agent_id})
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
                    
                    if (self.x, self.y) in self.found_items : 
                        print("/!\  this position was already found (1)")
                        print(f"found items: {len(self.found_items)}")
                    else: 
                        self.found_items.append((self.x, self.y))
                        print(f"found items: {len(self.found_items)}")   

            if msg["header"] == GET_NB_CONNECTED_AGENTS :
                self.nb_agents = msg["nb_connected_agents"]
                print("nb agents : ", self.nb_agents)
            
            if len(self.found_items) >= self.nb_agents*2 :
                print(f"------------------we all know where our stuff is : ---------------------\n found items: {len(self.found_items)}, \n items : {self.found_items} ")
                print(self.x, self.y)
                self.completed = True
                if self.key_discovered is False :
                    x_key, y_key = self.key_position
                    print(f"get my key at {self.key_position}")
                    self.move_to(x_key, y_key)
                    print("key done")
                    time.sleep(2)
                if self.box_discovered is False:
                    x_box, y_box = self.box_position
                    print(f"get my box at {self.box_position}")
                    self.move_to(x_box, y_box)
                    print("box done")
                    time.sleep(2)
                
                print("going to sleep for 5")
                time.sleep(5)

    #TODO: CREATE YOUR METHODS HERE...
    def search_closely(self, x_prec, y_prec, pre_cell_val, previous_direction):
        print("Starting Close search")
        found = False
        directions = {UP_RIGHT : (UP_LEFT, RIGHT, RIGHT, DOWN, DOWN),
                      UP_LEFT : (UP_RIGHT, LEFT,LEFT, DOWN, DOWN),
                      DOWN_RIGHT : (UP_RIGHT, DOWN,DOWN, LEFT, LEFT),
                      DOWN_LEFT : (UP_LEFT, DOWN, DOWN, RIGHT, RIGHT)}
        #dx = (x_new-x_prev)
        direction_dict = {(0,-1):(RIGHT, UP,LEFT, LEFT, DOWN),
                          (0,1):(RIGHT, DOWN,LEFT, LEFT, UP),
                          (-1,0):(UP, LEFT, DOWN, DOWN, RIGHT),
                          (1,0):(UP, RIGHT, DOWN, DOWN, LEFT),
                          (-1,-1):(UP_RIGHT, LEFT,LEFT, DOWN, DOWN),
                          (1,-1):(UP_LEFT, RIGHT, RIGHT, DOWN, DOWN), 
                          (-1,1):(UP_LEFT, DOWN, DOWN, RIGHT, RIGHT), 
                          (1,1) :(UP_RIGHT, DOWN,DOWN, LEFT, LEFT)}

        saved_x, saved_y = self.x, self.y
        for dir in directions[previous_direction] :
            if self.cell_val == 1.0 : # shouldn't happen, but just in case
                print("------found it first try !------------")
                found = True
                break
            cmds = {"header": MOVE,"direction": dir}
            self.network.send(cmds)
            time.sleep(0.5)
            if self.cell_val > pre_cell_val: # agent is getting closer, continue
                print("Got closer, next step...")
                time.sleep(0.5)
                print(f"now scanning {direction_dict[(self.x-saved_x, self.y-saved_y)]}")
                for new_dir in direction_dict[(self.x-saved_x, self.y-saved_y)]:
                    cmds = {"header": MOVE,"direction": new_dir}
                    self.network.send(cmds)
                    time.sleep(1)
                    if self.cell_val == 1.0 :
                        print("---------- found it --------------")
                        found = True
                        break
                if found : 
                    break
            time.sleep(0.5)
        if found :
            self.network.send({"header" : GET_ITEM_OWNER})
            print("going out")
            # Goes back to original position
            self.move_to(saved_x, saved_y)
            cmds = {"header": MOVE,"direction": previous_direction}

    def move_to_bounds_center(self):
        ymoy = int((self.ymin+self.ymax)/2)
        self.move_to(1, ymoy-1)
        print("I'm in place")

    def move_to(self, x, y):
        while (self.x != x) or (self.y != y):
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
            time.sleep(0.1)

    def scan_cell(self):
        print(f"scanning cell : ({self.x},{self.y}) -> value : {self.cell_val}")
        match self.cell_val :
            case 0.25 :
                print("close to a key")
            case 0.3 :
                print("close to a box")
            case 0.5 :
                print("I am very close to a key")
            case 0.6 :
                print("I'm very close to a box")
            case 1.0 :
                self.network.send({"header" : GET_ITEM_OWNER})
            case _: 
                print(".")
        return self.cell_val
    
    def game_state(self):
        print(f"Position clé : {self.key_position}, position box : {self.box_position} \n clé decouverte :{self.key_discovered}, box décoverte : {self.box_discovered}, complété : {self.completed} ")
        print(f"found items: {len(self.found_items)}")

    def check_walls(self, up_direction, down_direction):
        """checks for walls. If there is, changes the direction of the zigzags
        """
        if self.x >= self.w-3: 
            print("wall !")
            return UP_LEFT, DOWN_LEFT

        elif self.x <= 3 : 
            print("wall !")
            return UP_RIGHT, DOWN_RIGHT
        else :
            return up_direction, down_direction
        
    def forget_found_item(self):
        """forget item values after it was found
        """
        if not len(self.found_items) >= self.nb_agents*2 :
            for x_item, y_item in self.found_items : 
                if np.abs(self.x - x_item) <= 2 and np.abs(self.y-y_item) <= 2:
                    print("already found this one, forget it")
                    self.cell_val = 0.0
            print("cell_val : ", self.cell_val)

    def remember_found_item(self):
        for x_item, y_item in self.found_items :
            if np.abs(self.x - x_item) <= 2 and np.abs(self.y-y_item) <= 2:
                print("already found this one, forget it")
                self.cell_val = 1.0
        print("cell_val : ", self.cell_val)

    def get_nb_agents(self):
        self.network.send({"header":GET_NB_CONNECTED_AGENTS})
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()
    agent = Agent(args.server_ip)
    try:    #Automatic control
        print("Hi, i'm agent ", agent.agent_id +1)
        time.sleep(2)
        agent.get_nb_agents()
        agent.move_to_bounds_center()
        UP_LR, DOWN_LR = UP_RIGHT, DOWN_RIGHT #start by going right
        while True:
            while agent.searching : 
                while agent.y < agent.ymax-3 :
                    if agent.box_discovered and agent.key_discovered : 
                        print("I'm DONE")
                        agent.completed = True
                        break  
                    UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR)
                    cmds = {"header": MOVE,"direction": DOWN_LR}
                    agent.network.send(cmds)
                    time.sleep(0.3)
                    agent.forget_found_item()
                    time.sleep(0.3)
                    if agent.cell_val > 0 :
                        agent.search_closely(agent.x, agent.y, agent.cell_val, DOWN_LR)
                while agent.y >= agent.ymin+3:
                    if agent.box_discovered and agent.key_discovered : 
                        print("I'm DONE")
                        agent.completed = True
                        break 
                    UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR) #defines left or right direction
                    cmds = {"header": MOVE,"direction": UP_LR}
                    agent.network.send(cmds)
                    time.sleep(0.3)
                    agent.forget_found_item()
                    time.sleep(0.3)
                    if agent.cell_val > 0:
                        agent.search_closely(agent.x, agent.y, agent.cell_val, UP_LR)
                agent.game_state()
            if agent.completed : 
                cmds = {"header": MOVE,"direction": STAND}
                agent.network.send(cmds)
                time.sleep(10)
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



