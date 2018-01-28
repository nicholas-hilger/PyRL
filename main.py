import tdl
import random
from random import randint
from rect import Rect
from tile import *
import colors
import pygame
from game_object import *
import textwrap

SCREEN_WIDTH = 100
SCREEN_HEIGHT = 80

MAP_WIDTH = 100
MAP_HEIGHT = 72

ROOM_MAX_SIZE = 17
ROOM_MIN_SIZE = 9
MAX_ROOMS = 38

BAR_WIDTH = 20
PANEL_HEIGHT = 8
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

FPS = 30

FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10
MAX_ROOM_MONSTERS = 4

color_dark_wall = (30, 30, 30)
color_light_wall = (255, 255, 255)
color_dark_ground = (50, 50, 50)
color_light_ground = (100, 100, 100)

global fov_recompute
fov_recompute = True

def handle_keys():

    user_input = tdl.event.key_wait()
    global fov_recompute

    #Movement keys, only if the player isn't paused
    if game_state == 'playing':
        if user_input.key == 'UP' or user_input.key == 'KP8' or user_input.keychar == 'k':
            player.move_or_attack(0, -1, objects)
            fov_recompute = True
        elif user_input.key == 'DOWN' or user_input.key == 'KP2' or user_input.keychar == 'j':
            player.move_or_attack(0, 1, objects)
            fov_recompute = True
        elif user_input.key == 'RIGHT' or user_input.key == 'KP6' or user_input.keychar == 'l':
            player.move_or_attack(1, 0, objects)
            fov_recompute = True
        elif user_input.key == 'LEFT' or user_input.key == 'KP4' or user_input.keychar == 'h':
            player.move_or_attack(-1, 0, objects)
            fov_recompute = True
        #diagonal movement
        elif user_input.key == 'KP1':
            player.move_or_attack(-1, 1, objects)
            fov_recompute = True
        elif user_input.key == 'KP3':
            player.move_or_attack(1, 1, objects)
            fov_recompute = True
        elif user_input.key == 'KP7':
            player.move_or_attack(-1, -1, objects)
            fov_recompute = True
        elif user_input.key == 'KP9':
            player.move_or_attack(1, -1, objects)
            fov_recompute = True
        elif user_input.key == 'ESCAPE':
            return 'exit'
        else:
            return 'didnt-take-turn'

        '''elif user_input.key == 'ENTER' and user_input.alt:
            #Alt-enter toggles fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())'''


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
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, colors.dark_green, colors.dark_gray)

    #blit the contents of panel to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)

def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not GameObject.is_blocked(GameObject, x, y, my_map, objects):
            if randint(0, 100) < 80:
                #create a goblin
                monster_component = Fighter(hp=10, defense=0, strength=3, death_function=monster_death)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 'g', 'Goblin', colors.darker_green, my_map, objects, blocks=True, fighter=monster_component, ai=ai_component)
            else:
                #create a slug
                monster_component = Fighter(hp=14, defense=1, strength=2, death_function=monster_death)
                ai_component = BasicMonster()
                monster = GameObject(x, y, 's', 'Slug', colors.amber, my_map, objects, blocks=True, fighter=monster_component, ai=ai_component)
            objects.append(monster)


def player_death(player):
    global game_state
    print('You died!')
    game_state = 'dead'

    #turn the player into a corpse
    player.char = '%'
    player.color = colors.dark_red


def monster_death(monster):
    print(monster.name.capitalize() + ' collapses in a pile of gore.')
    monster.char = '%'
    monster.color = colors.crimson
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

fighter_component = Fighter(hp=100, defense=1, strength=5, death_function=player_death)
player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', 'Rogue', (255, 255, 255), my_map, objects, blocks=True, fighter=fighter_component)
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

while not tdl.event.is_window_closed():

    while not pygame.mixer.music.get_busy():
        print('Changing music')
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

    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for obj in objects:
            if obj.ai:
                obj.ai.take_turn(visible_tiles, player)
