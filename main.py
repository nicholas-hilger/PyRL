import tdl
import random
from random import randint
from rect import Rect
from tile import *
import colors
import pygame
import textwrap
import math

SCREEN_WIDTH = 100
SCREEN_HEIGHT = 80

MAP_WIDTH = 100
MAP_HEIGHT = 71

ROOM_MAX_SIZE = 17
ROOM_MIN_SIZE = 9
MAX_ROOMS = 38

BAR_WIDTH = 20
PANEL_HEIGHT = 9
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

FPS = 30

FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 15
MAX_ROOM_MONSTERS = 5

color_dark_wall = (30, 30, 30)
color_light_wall = (255, 255, 255)
color_dark_ground = (50, 50, 50)
color_light_ground = (100, 100, 100)

mouse_coord = (0, 0)

turns = 0

global fov_recompute
fov_recompute = True

def handle_keys():

    global fov_recompute
    global mouse_coord
    global turns

    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

    if not keypress:
        return 'didnt-take-turn'

    #Movement keys, only if the player isn't paused
    if game_state == 'playing':
        turns += 1
        if user_input.key == 'UP' or user_input.key == 'KP8' or user_input.keychar == 'k':
            player.move_or_attack(0, -1)
            fov_recompute = True
        elif user_input.key == 'DOWN' or user_input.key == 'KP2' or user_input.keychar == 'j':
            player.move_or_attack(0, 1)
            fov_recompute = True
        elif user_input.key == 'RIGHT' or user_input.key == 'KP6' or user_input.keychar == 'l':
            player.move_or_attack(1, 0)
            fov_recompute = True
        elif user_input.key == 'LEFT' or user_input.key == 'KP4' or user_input.keychar == 'h':
            player.move_or_attack(-1, 0)
            fov_recompute = True
        elif user_input.key == 'KP1':
            player.move_or_attack(-1, 1)
            fov_recompute = True
        elif user_input.key == 'KP3':
            player.move_or_attack(1, 1)
            fov_recompute = True
        elif user_input.key == 'KP7':
            player.move_or_attack(-1, -1)
            fov_recompute = True
        elif user_input.key == 'KP9':
            player.move_or_attack(1, -1)
            fov_recompute = True
        elif user_input.key == 'ESCAPE':
            return 'exit'
        else:
            return 'didnt-take-turn'

        '''elif user_input.key == 'ENTER' and user_input.alt:
            #Alt-enter toggles fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())'''


import math

class GameObject:
    #A generic object. Always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.my_map = my_map
        self.objects = objects
        self.fighter = fighter

        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        if not self.is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_or_attack(self, dx, dy):
        x = self.x + dx
        y = self.y + dy

        target = None
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter:
                target = obj
                break
        if target is not None:
            self.fighter.attack(target)
        else:
            self.move(dx, dy)

    def draw(self, con, vis_tiles):
        if(self.x, self.y) in vis_tiles:
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self, con):
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def is_blocked(self, x, y):
        if my_map[x][y].blocked:
            return True

        for obj in objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return True

        return False

    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction) then round it and
        #convert to int so the movement is restricted to the grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self, objects):
        objects.remove(self)
        objects.insert(0, self)

class Fighter:
    #Combat-related properties and methods
    def __init__(self, hp, defense, cut=0, blunt=0, pierce=0, magic=0, cut_res=1, blunt_res=1, pierce_res=1, magic_res=1, att=0, wis=0, xp=0, gold=0, spd = 1, death_function=None, lvl=1):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.cut = cut
        self.blunt = blunt
        self.pierce = pierce
        self.magic = magic
        self.cut_res = cut_res
        self.blunt_res = blunt_res
        self.pierce_res = pierce_res
        self.magic_res = magic_res
        self.xp = 0
        self.max_xp = xp
        self.death_function = death_function
        self.lvl = lvl
        self.wis = wis
        self.att = att
        self.gold = gold
        self.spd = spd

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            func = self.death_function
            if func is not None:
                func(self.owner)

    def attack(self, target):
        damage = 0
        if self.blunt > 0:
            damage += int((self.att + self.blunt) * target.fighter.blunt_res)
        if self.cut > 0:
            damage += int((self.att + self.cut) * target.fighter.cut_res)
        if self.pierce > 0:
            damage += int((self.att + self.pierce) * target.fighter.pierce_res)
        if self.magic > 0:
            damage += int((self.wis + self.magic) * target.fighter.magic_res)

        damage -= target.fighter.defense

        damage_type = max(self.blunt, self.cut, self.pierce)

        damage_adj = ' attacks '

        if damage_type == self.blunt:
            damage_adj = ' smashes '
        elif damage_type == self.pierce:
            damage_adj = ' stabs '
        elif damage_type == self.cut:
            damage_adj = ' slashes '

        if damage > 0:
            message(self.owner.name.capitalize() + damage_adj + target.name + ' for ' + str(damage) + ' damage.')
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' tries to attack ' + target.name + ', but whiffs!')

    def check_xp(self, player):
        if self.xp >= self.max_xp:
            self.xp -= self.max_xp
            self.max_xp = int(float(self.max_xp * 1.3))
            self.max_hp += 15
            self.hp += 10
            self.att += 1
            self.wis += 1
            self.lvl += 1
            message(player.name + ' is now level ' + str(player.fighter.lvl) + '!', colors.dark_green)

    def check_limits(self):
        if self.hp > self.max_hp:
            self.hp = self.max_hp

class BasicMonster():
    #AI for a basic monster
    def take_turn(self, visible_tiles, player):
        #if you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0 and turns % monster.fighter.spd == 0:
                monster.fighter.attack(player)



def get_names_under_mouse():
    global visible_tiles

    (x, y) = mouse_coord

    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]

    names = ', '.join(names) #join the names, seperated by commas
    return names.capitalize()


def create_room(room):
    global my_map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    global my_map
    for x in range(min(x1,x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global my_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False


def make_map():
    global my_map

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #assign random positions without going out of bounds
        x = randint(0, MAP_WIDTH-w-1)
        y = randint(0, MAP_HEIGHT-h-1)

        new_room = Rect(x, y, w, h)

        #run through other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            create_room(new_room)

            #center_coords of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the player's starting room
                player.x = new_x
                player.y = new_y

            else:
                #connect to the previous room with a tunnel

                #center coords of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #flip a coin
                if randint(0, 1):
                    #first move horizontally, then veritcally
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # first move horizontally, then vertically
                    create_v_tunnel(prev_y, new_y, new_x)
                    create_h_tunnel(prev_x, new_x, prev_y)

            #append the new room to the list
            place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1


def is_visible_tile(x, y):
    global my_map

    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked:
        return False
    elif my_map[x][y].block_sight:
        return False
    else:
        return True


def render_all():
    global fov_recompute
    global visible_tiles

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quick_fov(player.x, player.y, is_visible_tile, fov=FOV_ALGO, radius=TORCH_RADIUS, lightWalls=FOV_LIGHT_WALLS)

    #Go through all tiles, and set their rendering params according to the FOV
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = (x, y) in visible_tiles
            wall = my_map[x][y].block_sight
            if not visible:
                if my_map[x][y].explored:
                    if wall:
                        con.draw_char(x, y, '#', fg=color_dark_wall, bg=None)
                    else:
                        con.draw_char(x, y, '.', fg=color_dark_ground, bg=None)
            else:
                my_map[x][y].explored = True
                if wall:
                    con.draw_char(x, y, '#', fg=color_light_wall, bg=None)
                else:
                    con.draw_char(x, y, '.', fg=color_light_ground, bg=None)

    for obj in objects:
        if obj != player:
            obj.draw(con, visible_tiles)
    player.draw(con, visible_tiles)

    #blit the contents of "con" to the root console and display it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

    #clears the stats panel
    panel.clear(fg=colors.white, bg=colors.black)

    y = 1
    for(line, color) in game_msgs:
        panel.draw_str(MSG_X, y, line, bg=None, fg=color)
        y += 1

    #show the player's stats
    render_bar(1, 2, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, colors.dark_green, colors.dark_gray)
    render_bar(1, 3, BAR_WIDTH, 'XP', player.fighter.xp, player.fighter.max_xp, colors.dark_purple, colors.dark_gray)

    panel.draw_str(1, 1, player.name, fg=colors.white)
    panel.draw_str(15, 1, 'Lvl ' + str(player.fighter.lvl), fg=colors.green)

    panel.draw_str(1, 4, '$' + str(player.fighter.gold), fg=colors.yellow)
    panel.draw_str(10, 4, 'T:' + str(turns), fg=colors.white)

    panel.draw_str(1, 5, 'C:' + str(player.fighter.cut), fg=colors.red)
    panel.draw_str(7, 5, 'B:' + str(player.fighter.blunt), fg=colors.gray)
    panel.draw_str(12, 5, 'P:' + str(player.fighter.pierce), fg=colors.orange)
    panel.draw_str(17, 5, "M:" + str(player.fighter.magic), fg=colors.light_blue)

    panel.draw_str(1, 6, 'Cx' + str(player.fighter.cut_res), fg=colors.red)
    panel.draw_str(7, 6, 'Bx' + str(player.fighter.blunt_res), fg=colors.gray)
    panel.draw_str(12, 6, 'Px' + str(player.fighter.pierce_res), fg=colors.orange)
    panel.draw_str(17, 6, 'Mx' + str(player.fighter.magic_res), fg=colors.light_blue)

    panel.draw_str(1, 7, "Att:" + str(player.fighter.att), fg=colors.white)
    panel.draw_str(8, 7, "Wis:" + str(player.fighter.wis), fg=colors.white)
    panel.draw_str(15, 7, 'Def:' + str(player.fighter.defense), fg=colors.white)

    panel.draw_str(MSG_X, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    #blit the contents of panel to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)


def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not GameObject.is_blocked(GameObject, x, y):
            if randint(0, 100) < 80:
                #create a goblin
                monster_component = Fighter(hp=27, defense=2, cut=4, xp=8, spd=3, death_function=monster_death)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 'g', 'Goblin', colors.darker_green, blocks=True, fighter=monster_component, ai=ai_component)
            else:
                #create a slug
                monster_component = Fighter(hp=19, defense=1, blunt=2, xp=6, spd=2, death_function=monster_death)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 's', 'Slug', colors.amber, blocks=True, fighter=monster_component, ai=ai_component)
            objects.append(monster)


def player_death(player):
    global game_state
    message('You died!', colors.dark_red)
    game_state = 'dead'

    #turn the player into a corpse
    player.char = '%'
    player.color = colors.dark_red


def monster_death(monster):
    message(monster.name.capitalize() + ' collapses in a pile of gore.', colors.red)
    monster.char = '%'
    monster.color = colors.crimson
    player.fighter.xp += monster.fighter.max_xp
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = monster.name + '\'s remains'
    monster.send_to_back(objects)


def render_bar(x, y, tot_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * tot_width)

    panel.draw_rect(x, y, tot_width, 1, None, bg=back_color)

    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)

    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (tot_width-len(text))//2
    panel.draw_str(x, y, text, fg=colors.white, bg=None)


def message(new_msg, color = colors.white):
    #split the message into multiple lines, if need be
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        game_msgs.append((line, color))

#######################
#Init and Main Loop   #
#######################


tdl.set_font('Fonts/terminal10x10_gs_tc.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRL", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

objects = []

game_msgs = []

music_play = 1

my_map = [[Tile(True)
               for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

fighter_component = Fighter(hp=145, defense=1, blunt=5, xp=25, att=3, wis=2, gold=200, death_function=player_death)
player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', 'Rogue', (255, 255, 255), blocks=True, fighter=fighter_component)
objects.append(player)

message(player.name + ' has entered Floor 1 of Korum-Zal\'s domain.', colors.red)

make_map()

fov_recompute = True

game_state = 'playing'
player_action = None

pygame.mixer.init()
pygame.mixer.music.load("Music/" + random.choice([
    "Komiku Treasure Finding.mp3",
    "Lately Kind Of Yeah DRACULA.mp3",
    "Visager Eerie Mausoleum.mp3",
    "Visager Ice Cave.mp3"
    ]))
pygame.mixer.music.play()

render_all()

mouse_coord = (0, 0)

tdl.set_fps(30)

while not tdl.event.is_window_closed():

    while not pygame.mixer.music.get_busy():
        pygame.mixer.music.load("Music/" + random.choice([
            "Komiku Treasure Finding.mp3",
            "Lately Kind Of Yeah DRACULA.mp3",
            "Visager Eerie Mausoleum.mp3",
            "Visager Ice Cave.mp3"
        ]))
        pygame.mixer.music.play()

    render_all()

    tdl.flush()

    for obj in objects:
        obj.clear(con)

    #Handle keys and exit the game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    player.fighter.check_xp(player)
    player.fighter.check_limits()

    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for obj in objects:
            if obj.ai:
                if turns % obj.fighter.spd == 0:
                    obj.ai.take_turn(visible_tiles, player)
