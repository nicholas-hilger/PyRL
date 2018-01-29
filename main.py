import tdl
import random
from random import randint
from rect import Rect
from tile import *
import colors
import pygame
from config import *
from utils import *
from game_object import *
from death_functions import *

mouse_coord = (0, 0)

turns = 0
last_combat = 0

global fov_recompute
fov_recompute = True



def handle_keys():

    global fov_recompute
    global mouse_coord
    global turns
    global last_combat

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
            player.move_or_attack(0, -1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'DOWN' or user_input.key == 'KP2' or user_input.keychar == 'j':
            player.move_or_attack(0, 1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'RIGHT' or user_input.key == 'KP6' or user_input.keychar == 'l':
            player.move_or_attack(1, 0, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'LEFT' or user_input.key == 'KP4' or user_input.keychar == 'h':
            player.move_or_attack(-1, 0, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'KP1':
            player.move_or_attack(-1, 1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'KP3':
            player.move_or_attack(1, 1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'KP7':
            player.move_or_attack(-1, -1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'KP9':
            player.move_or_attack(1, -1, objects, message, my_map, player)
            fov_recompute = True
        elif user_input.key == 'ESCAPE':
            return 'exit'
        else:
            return 'didnt-take-turn'

        '''elif user_input.key == 'ENTER' and user_input.alt:
            #Alt-enter toggles fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())'''

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
                        con.draw_char(x, y, '#', fg=colors.dark_gray, bg=None)
                    else:
                        con.draw_char(x, y, '.', fg=colors.darkest_gray, bg=None)
            else:
                my_map[x][y].explored = True
                if wall:
                    con.draw_char(x, y, '#', fg=colors.white, bg=None)
                else:
                    con.draw_char(x, y, '.', fg=colors.gray, bg=None)

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
    render_bar(1, 2, BAR_WIDTH, 'HP', player.hp, player.max_hp, colors.dark_green, colors.dark_gray)
    render_bar(1, 3, BAR_WIDTH, 'XP', player.xp, player.max_xp, colors.dark_purple, colors.dark_gray)

    panel.draw_str(1, 1, player.name, fg=colors.white)
    panel.draw_str(15, 1, 'Lvl ' + str(player.lvl), fg=colors.green)

    panel.draw_str(1, 4, '$' + str(player.gold), fg=colors.yellow)
    panel.draw_str(10, 4, 'T:' + str(turns), fg=colors.white)

    panel.draw_str(1, 5, 'C:' + str(player.cut), fg=colors.red)
    panel.draw_str(7, 5, 'B:' + str(player.blunt), fg=colors.light_gray)
    panel.draw_str(12, 5, 'P:' + str(player.pierce), fg=colors.orange)
    panel.draw_str(17, 5, "M:" + str(player.magic), fg=colors.light_azure)

    panel.draw_str(1, 6, 'Cx' + str(player.cut_weak), fg=colors.red)
    panel.draw_str(7, 6, 'Bx' + str(player.blunt_weak), fg=colors.light_gray)
    panel.draw_str(12, 6, 'Px' + str(player.pierce_weak), fg=colors.orange)
    panel.draw_str(17, 6, 'Mx' + str(player.magic_weak), fg=colors.light_azure)

    panel.draw_str(1, 7, "Att:" + str(player.att), fg=colors.white)
    panel.draw_str(8, 7, "Wis:" + str(player.wis), fg=colors.white)
    panel.draw_str(15, 7, 'Def:' + str(player.defense), fg=colors.white)

    panel.draw_str(MSG_X, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    #blit the contents of panel to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)


def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not GameObject.is_blocked(GameObject, x, y, my_map, objects):
            monster = random.choice([
                Goblin,
                Slug,
                Skeleton
            ])
            monster_instance = monster(x, y)
            objects.append(monster_instance)





def render_bar(x, y, tot_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * tot_width)

    panel.draw_rect(x, y, tot_width, 1, None, bg=back_color)

    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)

    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (tot_width-len(text))//2
    panel.draw_str(x, y, text, fg=colors.white, bg=None)




#######################
#Init and Main Loop   #
#######################


tdl.set_font('Fonts/terminal10x10_gs_tc.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRL", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

objects = []


music_play = 1

my_map = [[Tile(True)
               for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

player = Fighter(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, char='@', name='Rogue', color=colors.white, blocks=True, hp=145, defense=1, blunt=5, xp=50, att=3, wis=2, gold=200, death_function=player_death)
#player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', 'Rogue', (255, 255, 255), blocks=True, fighter=fighter_component)
objects.append(player)

message(player.name + ' has entered Floor 1 of Korum-Zal\'s domain.', colors.red)

make_map()

fov_recompute = True

game_state = 'playing'
player_action = None

pygame.mixer.init()
mus = ("Music/" + random.choice([
            "Komiku Treasure Finding.mp3",
            "Komiku_-_51_-_Chocolate_Valley.mp3",
            "Komiku_-_52_-_Cave_of_time.mp3",
            "Visager Ice Cave.mp3"
        ]))
print('Now Playing ' + mus)
pygame.mixer.music.load(mus)
pygame.mixer.music.play()

render_all()

mouse_coord = (0, 0)

tdl.set_fps(30)

while not tdl.event.is_window_closed():

    while not pygame.mixer.music.get_busy():
        mus = ("Music/" + random.choice([
            "Komiku Treasure Finding.mp3",
            "Komiku_-_51_-_Chocolate_Valley.mp3",
            "Komiku_-_52_-_Cave_of_time.mp3",
            "Visager Ice Cave.mp3"
        ]))
        print('Now Playing ' + mus)
        pygame.mixer.music.load(mus)
        pygame.mixer.music.play()

    render_all()

    tdl.flush()

    for obj in objects:
        obj.clear(con)

    #Handle keys and exit the game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    player.check_xp(player, message)
    player.check_limits()

    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for obj in objects:
            if obj.ai:
                if turns % obj.spd == 0:
                    obj.ai.take_turn(visible_tiles, player, turns, message, my_map, objects)
