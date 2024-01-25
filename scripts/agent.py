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
        self.ymin, self.ymax = env_conf["attribution"] # Map restrictions attributed to this agent
        Thread(target=self.msg_cb, daemon=True).start()

    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            if msg["header"]==MOVE: # Update position and cell value
                self.x=msg["x"]
                self.y=msg["y"]
                self.cell_val=msg["cell_val"]
            
            if msg["header"] == BROADCAST_MSG : # Handle a broadcast message
                if msg["msg type"] == KEY_DISCOVERED :
                    self.key_position_list[msg["owner"]] = True
                    if msg["owner"] == self.agent_id: # My key has been found
                        self.key_position = msg["position"]
                elif msg["msg type"] == BOX_DISCOVERED :
                    self.box_position_list[msg["owner"]] = True
                    if msg["owner"] == self.agent_id : # My box has been found
                        self.box_position = msg["position"]
                # Always keep count of the number of items found in the game
                if (self.x, self.y) not in self.found_items : 
                    self.found_items.append((self.x, self.y))

            # If the broadcast message says it found the item of the concerned agent
            if msg["header"] == GET_ITEM_OWNER :
                if msg["type"] == KEY_TYPE :
                    self.key_position_list[msg["owner"]] = True
                    if msg["owner"] == self.agent_id :
                        self.key_position = [self.x, self.y]
                        self.key_discovered = True 
                elif msg["type"] == BOX_TYPE :
                    self.box_position_list[msg["owner"]] = True 
                    if msg["owner"] == self.agent_id :
                        self.box_position = [self.x, self.y]
                        self.box_discovered = True
                self.found_items.append((self.x, self.y))
                print(f"found items: {self.found_items}")
                self.network.send({"header": BROADCAST_MSG,
                                        "msg type": msg["type"]+1,
                                        "position":(self.x, self.y),
                                        "owner": msg["owner"]})

            if msg["header"] == GET_NB_CONNECTED_AGENTS :
                self.nb_agents = msg["nb_connected_agents"]
                print("nb agents : ", self.nb_agents)
                self.key_position_list = [False for i in range(self.nb_agents)]
                self.box_position_list = [False for i in range(self.nb_agents)]
        
    #TODO: CREATE YOUR METHODS HERE...
    def go_to_final_position(self) :
            """once all the agents know where their items are, they stop searching and go to find their missing items
            """
            print("Le jeu est terminé, je vais à ma position finale")
            if not self.key_discovered :
                self.move_to(self.key_position[0], self.key_position[1])
                self.network.send({"header" : GET_ITEM_OWNER})
                self.key_discovered = True
                time.sleep(2)

            self.move_to(self.box_position[0], self.box_position[1])
            self.network.send({"header" : GET_ITEM_OWNER})
            self.box_discovered = True
            time.sleep(15)

    def search_closely(self, pre_cell_val, previous_direction):
        """This function is called when an angent comes close to an item.
        It follows a special strategy to progress towards the highest potential, which is the item.

        Args:
            pre_cell_val : cell value when the function is called.
            previous_direction : the move of the agent just before calling the function.
        """
        found = False
        directions = {UP_RIGHT : (UP_LEFT, RIGHT, RIGHT, DOWN, DOWN),
                      UP_LEFT : (UP_RIGHT, LEFT,LEFT, DOWN, DOWN),
                      DOWN_RIGHT : (UP_RIGHT, DOWN,DOWN, LEFT, LEFT),
                      DOWN_LEFT : (UP_LEFT, DOWN, DOWN, RIGHT, RIGHT),
                      RIGHT : (UP, RIGHT,DOWN, DOWN, LEFT)}
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
            if self.cell_val == 1.0 :
                print("------found it first try !------------")
                found = True
                break
            cmds = {"header": MOVE,"direction": dir}
            self.network.send(cmds)
            time.sleep(0.5)
            if self.cell_val > pre_cell_val: # agent is getting closer, continue searching
                if self.cell_val == 1.0 :
                    print("------found it 2nd try !------------")
                    found = True
                    break
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
            # Goes back to original position, before close_search() was called.
            self.move_to(saved_x, saved_y)
            cmds = {"header": MOVE,"direction": previous_direction}

    def move_to_bounds_center(self):
        ymoy = int((self.ymin+self.ymax)/2)
        self.move_to(1, ymoy)
        print("I'm in place")

    def move_to(self, x, y):
        """Makes the agent move to a given position

        Args:
            x (int): horizontal wanted position
            y (int): vertical wanted position
        """
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
    
    def game_state(self):
        """prints useful information in the console for the concerned agent.
        """
        print(f"Position clé : {self.key_position}, position box : {self.box_position} \n clé decouverte :{self.key_discovered}, box décoverte : {self.box_discovered}, complété : {self.completed} ")
        print(f"found items: {len(self.found_items)}")

    def check_walls(self, up_direction, down_direction):
        """checks for walls. If there is one, changes the direction (left or right) of the zigzags

        Args:
            up_direction (int): previous upwards direction the robot was using 
            down_direction (int): same for downwards direction

        Returns:
            (int, int): updated directions given in the arguments
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
        #We add sleep times to give the program enough time to synchronize between every thread 
        time.sleep(2)
        agent.get_nb_agents()
        time.sleep((agent.agent_id+1)/2)
        agent.move_to_bounds_center()
        bord = 3
        if agent.nb_agents>= 4 : 
            bord = 2
        # Special strategy for 4 agents : the agents go in a straight line
        if agent.nb_agents >= 5 : 
            while ((False in agent.box_position_list) or (False in agent.key_position_list)):
                if agent.box_discovered and agent.key_discovered : 
                    print("I'm DONE")
                    agent.completed = True
                    break 
                elif agent.x == agent.w :
                    cmds = {"header": MOVE,"direction": STAND}
                    agent.network.send(cmds)
                    time.sleep(1)
                else:
                    agent.forget_found_item()
                    time.sleep(0.3)
                    if agent.cell_val > 0 :
                        agent.search_closely(agent.cell_val, RIGHT)
                    time.sleep(0.3)
                    cmds = {"header": MOVE,"direction": RIGHT}
                    agent.network.send(cmds)
                time.sleep(0.4)
                print("position lists for key and box : ", agent.key_position_list, agent.box_position_list )
        # Zig Zag strategy for less agents
        else : 
            UP_LR, DOWN_LR = UP_RIGHT, DOWN_RIGHT # the agent starts by going from left to right
            while ((False in agent.box_position_list) or (False in agent.key_position_list)):
                """The zig zag strategy uses 2 while loops : 
                The first one is "agent moves until it gets to the top of its zone"
                The second loop is "[...] until the bottom of its zone".
                """
                while agent.y < agent.ymax-bord :
                    # Stops the loop once both items are discovered
                    if agent.box_discovered and agent.key_discovered :
                        print("I'm DONE")
                        agent.completed = True
                        break
                    agent.forget_found_item()
                    time.sleep(0.3)
                    if agent.cell_val > 0 :
                        agent.search_closely(agent.cell_val, DOWN_LR)
                    UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR)
                    cmds = {"header": MOVE,"direction": DOWN_LR}
                    agent.network.send(cmds)
                    time.sleep(0.3)

                while agent.y >= agent.ymin+bord:
                    if agent.box_discovered and agent.key_discovered : 
                        print("I'm DONE")
                        agent.completed = True
                        break 
                    agent.forget_found_item()
                    time.sleep(0.3)
                    if agent.cell_val > 0 :
                        agent.search_closely(agent.cell_val, UP_LR)
                    UP_LR, DOWN_LR = agent.check_walls(UP_LR, DOWN_LR) #defines left or right direction
                    cmds = {"header": MOVE,"direction": UP_LR}
                    agent.network.send(cmds)
                    time.sleep(0.3)
                    
                agent.game_state() 
        # Once the loop is broken, it means every agent knows where its items are.
        # The following method makes the go and fetch their keys and boxes.
        agent.go_to_final_position()
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