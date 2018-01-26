import tdl
from game_object import GameObject
from random import *
from rect import Rect
from tile import *
import colors

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 12
ROOM_MIN_SIZE = 7
MAX_ROOMS = 32

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
            player.move(0, -1)
            fov_recompute = True
        elif user_input.key == 'DOWN' or user_input.key == 'KP2' or user_input.keychar == 'j':
            player.move(0, 1)
            fov_recompute = True
        elif user_input.key == 'RIGHT' or user_input.key == 'KP6' or user_input.keychar == 'l':
            player.move(1, 0)
            fov_recompute = True
        elif user_input.key == 'LEFT' or user_input.key == 'KP4' or user_input.keychar == 'h':
            player.move(-1, 0)
            fov_recompute = True
        elif user_input.key == 'KP1':
            player.move(-1, 1)
            fov_recompute = True
        elif user_input.key == 'KP3':
            player.move(1, 1)
            fov_recompute = True
        elif user_input.key == 'KP7':
            player.move(-1, -1)
            fov_recompute = True
        elif user_input.key == 'KP9':
            player.move(1, -1)
            fov_recompute = True
        else:
            return 'didnt-take-turn'

    '''if user_input.key == 'ENTER' and user_input.alt:
        #Alt-enter toggles fullscreen
        tdl.set_fullscren(not tdl.get_fullscreen())'''

    if user_input.key == 'ESCAPE':
        return 'exit'


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
                    # first move horizontally, then veritcally
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
        obj.draw(con, visible_tiles)

    #blit the contents of "con" to the root console and display it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)


def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if randint(0, 100) < 80 and not GameObject.is_blocked(GameObject, x, y, my_map, objects):
            #create a goblin
            monster = GameObject(x, y, 'g', 'Goblin', colors.darker_green, my_map, objects, blocks=True)
        else:
            #create a slug
            monster = GameObject(x, y, 's', 'Slug', colors.amber, my_map, objects, blocks=True)
        objects.append(monster)

#######################
#Init and Main Loop   #
#######################


tdl.set_font('Fonts/terminal10x10_gs_tc.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)

objects = []

my_map = [[Tile(True)
               for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', 'Rogue', (255, 255, 255), my_map, objects, blocks=True)
objects.append(player)

make_map()

fov_recompute = True

game_state = 'playing'
player_action = None

while not tdl.event.is_window_closed():

    render_all()

    tdl.flush()

    for obj in objects:
        obj.clear(con)

    #Handle keys and exit the game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break
