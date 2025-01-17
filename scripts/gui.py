__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2023"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

import pygame, os
from my_constants import *    

img_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "img")

class GUI:
    def __init__(self, game, fps=10, cell_size=40):
        self.game = game
        self.w, self.h = self.game.map_w, self.game.map_h
        self.fps = fps
        self.clock = pygame.time.Clock()
        self.cell_size = cell_size
        self.screen_res = (self.w*cell_size*2, self.h*cell_size)      
        nb_agents = self.game.nb_agents
        map_h = self.h/nb_agents
        self.map_attribution = {}
        for i in range(nb_agents):
            h_limit1 = i*map_h
            h_limit2 = (i+1)*map_h
            self.map_attribution[i] = (int(h_limit1), int(h_limit2)) #defines the bounds in which the robot needs to scan

    def on_init(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_res)
        pygame.display.set_icon(pygame.image.load(img_folder + "/icon.png"))
        pygame.display.set_caption("IN512 Project")
        self.create_items()        
        self.running = True

    def dessiner_tableau(self, nb_joueurs):
        # Calculer la taille du tableau en fonction du nombre de joueurs
        nb_colonnes = nb_joueurs + 1
        largeur_colonne = ((self.w*self.cell_size*2-self.cell_size) - (self.w*self.cell_size+self.cell_size)) / nb_colonnes
        hauteur_ligne = 2*self.cell_size
        # Coordonnées du coin supérieur gauche et inférieur droit du tableau
        coin_sup_gauche = ((self.w+1)*self.cell_size, 5*self.cell_size)
        coin_inf_droit = ((self.w+1)*self.cell_size+nb_colonnes*largeur_colonne, 5*self.cell_size+5*hauteur_ligne)
        # Dessiner le fond du tableau
        pygame.draw.rect(self.screen, WHITE, (coin_sup_gauche, (coin_inf_droit[0] - coin_sup_gauche[0], coin_inf_droit[1] - coin_sup_gauche[1])))
        # Dessiner les lignes du tableau
        for i in range(1, nb_colonnes):
            x = coin_sup_gauche[0] + i * largeur_colonne
            pygame.draw.line(self.screen, BLACK, (x, coin_sup_gauche[1]), (x, coin_inf_droit[1]), 2)
       
        for i in range(1, 5):
            y = coin_sup_gauche[1] + i * hauteur_ligne
            pygame.draw.line(self.screen, BLACK, (coin_sup_gauche[0], y), (coin_inf_droit[0], y), 2)

        noms_lignes = ['id', 'key_position', 'box_position', 'key_discovered', 'box_discovered']
        for i, nom in enumerate(noms_lignes):
            x = coin_sup_gauche[0] + largeur_colonne / 2
            y = coin_sup_gauche[1] + i * hauteur_ligne + hauteur_ligne / 2
            font = pygame.font.Font(None, 24)
            texte = font.render(nom, True, BLACK)
            rect = texte.get_rect(center=(x, y))
            self.screen.blit(texte, rect)

        attributs = ['id', 'keys_positions', 'boxes_positions', 'keys_discovered', 'boxes_discovered']
       
        # Attributs des agents
        for i in range(self.game.nb_agents):
            #agent = self.game.agents[i]
            for j, attribut in enumerate(attributs):
                if attribut == 'id' :
                    valeur = str(self.game.agents[i].id)
                else :
                    valeur = str(getattr(self.game, attribut)[i])
                x = coin_sup_gauche[0] + (i+1) * largeur_colonne + largeur_colonne / 2
                y = coin_sup_gauche[1] + j * hauteur_ligne + hauteur_ligne / 2
                font = pygame.font.Font(None, 24)
                texte = font.render(valeur, True, BLACK)
                rect = texte.get_rect(center=(x, y))
                self.screen.blit(texte, rect)
    def create_items(self):
        #box
        box_img = pygame.image.load(img_folder + "/box.png")
        box_img = pygame.transform.scale(box_img, (self.cell_size, self.cell_size))
        self.boxes = [box_img.copy() for _ in range(self.game.nb_agents)]
        #keys
        key_img = pygame.image.load(img_folder + "/key.png")
        key_img = pygame.transform.scale(key_img, (self.cell_size, self.cell_size))
        self.keys = [key_img.copy() for _ in range(self.game.nb_agents)]
        #agent text number
        font = pygame.font.SysFont("Arial", self.cell_size//4, True)
        self.text_agents = [font.render(f"{i+1}", True, self.game.agents[i].color) for i in range(self.game.nb_agents)]
        #agent_img
        agent_img = pygame.image.load(img_folder + "/robot.png")
        agent_img = pygame.transform.scale(agent_img, (self.cell_size, self.cell_size))
        self.agents = [agent_img.copy() for _ in range(self.game.nb_agents)]

    
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

    
    def on_cleanup(self):
        pygame.event.pump()
        pygame.quit()
    

    def render(self):
        try:
            self.on_init()
            while self.running:
                for event in pygame.event.get():
                    self.on_event(event)    
                self.draw()
                self.clock.tick(self.fps)
            self.on_cleanup()
        except Exception:
            pass
    
    def color_cell(self, col, row, id_robot) :
        pygame.draw.rect(self.screen, self.game.agents[id_robot].color, (col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))
        pygame.draw.rect(self.screen, BLACK, (col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size), 1)
    def draw(self):
        self.screen.fill(BG_COLOR)

        #Grid
        for i in range(1, self.h):
            pygame.draw.line(self.screen, BLACK, (0, i*self.cell_size), (self.w*self.cell_size, i*self.cell_size))
        for j in range(1, self.w):
            pygame.draw.line(self.screen, BLACK, (j*self.cell_size, 0), (j*self.cell_size, self.h*self.cell_size))
        cases = []
        for i in range(self.game.nb_agents):   
            self.game.agents[i].history.append([self.game.agents[i].x, self.game.agents[i].y])
            for c in range (len(self.game.agents[i].history)):
                if [self.game.agents[i].history[c][0], self.game.agents[i].history[c][1]] not in self.game.all_items_positions :
                    self.color_cell(self.game.agents[i].history[c][0], self.game.agents[i].history[c][1], i)
                #self.display_coef()  
                if self.game.agents[i].history[c] not in cases :
                    cases.append(self.game.agents[i].history[c])
            #keys
            pygame.draw.rect(self.screen, self.game.agents[i].color, (self.game.keys[i].x*self.cell_size, self.game.keys[i].y*self.cell_size, self.cell_size, self.cell_size), width=3)
            self.screen.blit(self.keys[i], self.keys[i].get_rect(topleft=(self.game.keys[i].x*self.cell_size, self.game.keys[i].y*self.cell_size)))
            
            #boxes
            pygame.draw.rect(self.screen, self.game.agents[i].color, (self.game.boxes[i].x*self.cell_size, self.game.boxes[i].y*self.cell_size, self.cell_size, self.cell_size), width=3)
            self.screen.blit(self.boxes[i], self.boxes[i].get_rect(topleft=(self.game.boxes[i].x*self.cell_size, self.game.boxes[i].y*self.cell_size)))
            
            #agents
            self.screen.blit(self.agents[i], self.agents[i].get_rect(center=(self.game.agents[i].x*self.cell_size + self.cell_size//2, self.game.agents[i].y*self.cell_size + self.cell_size//2)))
            self.screen.blit(self.text_agents[i], self.text_agents[i].get_rect(center=(self.game.agents[i].x*self.cell_size + self.cell_size-self.text_agents[i].get_width()//2, self.game.agents[i].y*self.cell_size + self.cell_size-self.text_agents[i].get_height()//2)))

            self.split_map()
        font = pygame.font.Font(None, 36)
        text = "Nombre de cases jouées : " + str(len(cases))
        surface_texte = font.render(text, True, (0, 0, 0))  
        position_texte = (self.w*self.cell_size+3*self.cell_size, 3*self.cell_size)
        self.screen.blit(surface_texte, position_texte)
        self.dessiner_tableau(self.game.nb_agents)

        pygame.display.update()

    def split_map(self):
        """split map by the number of agents on the server, in this way, they work together to scan the area.

        TODO : should memorize which div is made for which agent.
        """
        nb_agents = self.game.nb_agents
        map_h = self.h/nb_agents
        map_w = self.w
        
        for i in range(nb_agents+1):
            h_limit1 = i*map_h*self.cell_size
            pygame.draw.line(self.screen, RED, (0, h_limit1 ), (map_w*self.cell_size, h_limit1))
            if i< nb_agents :
                agent=f"agent{i}"
                h_limit2 = (i+1)*map_h*self.cell_size
                self.map_attribution[agent] = (h_limit1, h_limit2) #defines the bounds in which the robot needs to scan
