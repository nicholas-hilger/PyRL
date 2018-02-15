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
from tcod import image_load
import shelve

mouse_coord = (0, 0)

turns = 0
last_combat = 0
inv_open = 0



global fov_recompute
fov_recompute = True


def handle_keys():

    global fov_recompute
    global mouse_coord
    global turns
    global last_combat
    global inv_open

    keypress = False
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

    if not keypress:
        return 'didnt-take-turn'

    if game_state == 'playing':
        if user_input.key == 'ESCAPE':
            return 'exit'
        '''if user_input.key == 'ENTER' and user_input.alt:
            # Alt-enter toggles fullscreen
            tdl.set_fullscreen(not tdl.get_fullscreen())'''

    #Movement keys, only if the player isn't paused
    if game_state == 'playing' and player.hp > 0:
        if user_input.key == 'UP' or user_input.key == 'KP8' or user_input.keychar == 'k':
            player.move_or_attack(0, -1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'DOWN' or user_input.key == 'KP2' or user_input.keychar == 'j':
            player.move_or_attack(0, 1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'RIGHT' or user_input.key == 'KP6' or user_input.keychar == 'l':
            player.move_or_attack(1, 0, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'LEFT' or user_input.key == 'KP4' or user_input.keychar == 'h':
            player.move_or_attack(-1, 0, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'KP1':
            player.move_or_attack(-1, 1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'KP3':
            player.move_or_attack(1, 1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'KP7':
            player.move_or_attack(-1, -1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        elif user_input.key == 'KP9':
            player.move_or_attack(1, -1, objects, message, my_map, player)
            fov_recompute = True
            turns += 1
        else:
            if user_input.text == 'g':
                for obj in objects:
                    if obj.x == player.x and obj.y == player.y and obj.item:
                        obj.pick_up(inventory, message, objects, player)
                        break
            elif user_input.text == '1':
                inv_open = 1
                chosen_item = inventory_menu('INVENTORY: Press a key next to an item to use/equip it, or anything else to cancel.')
                if chosen_item is not None:
                    if chosen_item.type == '':
                        chosen_item.use(inventory, message)
                    else:
                        chosen_item.equip(player, message, inventory)
            elif user_input.text == '2':
                chosen_item = consumables_menu("CONSUMABLES: Press a key next to an item to use it, or anything else to cancel.")
                if chosen_item is not None:
                    chosen_item.use(inventory, message)
            elif user_input.text == '3':
                chosen_item = equips_menu("EQUIPMENT: Press a key next to an item to equip it, or anything else to cancel.")
                if chosen_item is not None:
                    chosen_item.equip(player, message, inventory)
            elif user_input.text == '4':
                chosen_item = inventory_menu("DROP: Press a key next to an item to drop it, or anything else to cancel.")
                if chosen_item is not None:
                    chosen_item.drop(inventory, objects, message, player)
            elif user_input.text == '5':
                chosen_item = unequip_menu("UNEQUIP: Press a key next to a piece of equipment to unequip it, or anything else to cancel.")
                if chosen_item is not None:
                    chosen_item.unequip(player, message, inventory, objects)
            return 'didnt-take-turn'


def get_names_under_mouse():
    global visible_tiles

    (x, y) = mouse_coord

    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]

    names = ', '.join(names) #join the names, seperated by commas
    return names


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
    global my_map, objects

    objects = [player]

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

    if player.wep is not None:
        wep_show = player.wep.name
        wep_color = player.wep.color
    else:
        wep_show = 'None'
        wep_color = colors.dark_gray
    if player.shield is not None:
        shield_show = player.shield.name
        shield_color = player.shield.color
    else:
        shield_show = 'None'
        shield_color = colors.dark_gray
    if player.chest is not None:
        chest_show = player.chest.name
        chest_color = player.chest.color
    else:
        chest_show = 'None'
        chest_color = colors.dark_gray
    if player.pants is not None:
        pants_show = player.pants.name
        pants_color = player.pants.color
    else:
        pants_show = 'None'
        pants_color = colors.dark_gray
    if player.helm is not None:
        helm_show = player.helm.name
        helm_color = player.helm.color
    else:
        helm_show = 'None'
        helm_color = colors.dark_gray

    panel.draw_str(23, 2, "Weapon: " + str(wep_show), fg=wep_color)
    panel.draw_str(23, 3, 'Shield: ' + str(shield_show), fg=shield_color)
    panel.draw_str(23, 4, 'Helmet: ' + str(helm_show), fg=helm_color)
    panel.draw_str(23, 5, 'Chest:  ' + str(chest_show), fg=chest_color)
    panel.draw_str(23, 6, 'Pants:  ' + str(pants_show), fg=pants_color)

    panel.draw_str(MSG_X, 0, get_names_under_mouse(), bg=None, fg=colors.light_gray)

    #blit the contents of panel to the root console
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)


def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)
    num_items = randint(0, MAX_ROOM_ITEMS)
    item_chance = randint(0, 100)

    for i in range(num_monsters):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not GameObject.is_blocked(x, y, my_map, objects):
            monster = random.choice([
                Goblin,
                Slug,
                LesserGhoul,
                Imp
            ])
            monster_instance = monster(x, y)
            objects.append(monster_instance)

    for i in range(num_items):
        x = randint(room.x1 + 1, room.x2 - 1)
        y = randint(room.y1 + 1, room.y2 - 1)

        if not GameObject.is_blocked(x, y, my_map, objects) and item_chance < ITEM_CHANCE:
            place_item(x, y)


def render_bar(x, y, tot_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * tot_width)

    panel.draw_rect(x, y, tot_width, 1, None, bg=back_color)

    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_color)

    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (tot_width-len(text))//2
    panel.draw_str(x, y, text, fg=colors.white, bg=None)


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options')

    #Calculate the total height for the header (after textwrap) and one line per option
    header_wrapped = []
    for header_line in header.splitlines():
        header_wrapped.extend(textwrap.wrap(header_line, width))
    header_height = len(header_wrapped)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    #print the header, with wrapped text
    window = tdl.Console(width, height)
    window.draw_rect(0, 0, width, height, None, fg=colors.white, bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(0, 0+i, header_wrapped[i])

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        window.draw_str(0, y, text, bg=None)
        y += 1
        letter_index += 1

    #blit these contents to the root console
    x = SCREEN_WIDTH//2 - width//2
    y = 0
    root.blit(window, x, y, width, height, 0, 0)

    #present the root console to the player and wait for a key-press
    tdl.flush()
    key = tdl.event.key_wait()
    key_char = key.char
    if key_char == '':
        key_char = ' ' #a placeholder

    index = ord(key_char) - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def inventory_menu(header):
    if len(inventory) == 0:
        options = ['You don\'t have anything']
    else:
        options = [item.name for item in inventory]

    index = menu(header, options, INVENTORY_WIDTH)

    if index is None or len(inventory) == 0:
        return None
    return inventory[index]


def consumables_menu(header):
    global consumables
    consumables.clear()

    for i in inventory:
        if i.type == '':
            consumables.append(i)

    if len(consumables) == 0:
        options = ['You don\'t have any consumables']
    else:
        options = [item.name for item in consumables]

    index = menu(header, options, INVENTORY_WIDTH)

    if index is None or len(consumables) == 0:
        return None
    return consumables[index]


def equips_menu(header):
    global equips
    equips.clear()

    for i in inventory:
        if i.type != '':
            equips.append(i)

    if len(equips) == 0:
        options = ['You don\'t have any equipment']
    else:
        options = [item.name for item in equips]

    index = menu(header, options, INVENTORY_WIDTH)

    if index is None or len(equips) == 0:
        return None
    return equips[index]


def unequip_menu(header):
    current_equips = []

    if player.wep is not None:
        current_equips.append(player.wep)
    if player.shield is not None:
        current_equips.append(player.shield)
    if player.helm is not None:
        current_equips.append(player.helm)
    if player.chest is not None:
        current_equips.append(player.chest)
    if player.pants is not None:
        current_equips.append(player.pants)

    if len(current_equips) == 0:
        options = ['You don\'t have anything equipped']
    else:
        options = [item.name for item in current_equips]

    index = menu(header, options, INVENTORY_WIDTH)

    if index is None or len(current_equips) == 0:
        return None
    return current_equips[index]


def cast_heal():
    if player.hp == player.max_hp:
        message('You\'re already at full health!', colors.light_red)
        return 'cancelled'

    message('Your wounds feel healed.', colors.light_violet)
    player.heal(int(player.max_hp/4))


def cast_lesser_heal():
    if player.hp == player.max_hp:
        message('You\'re already at full health!', colors.light_red)
        return 'cancelled'

    message('Your feel slightly healed.', colors.light_violet)
    player.heal(int(player.max_hp/10))


def cast_greater_heal():
    if player.hp == player.max_hp:
        message('You\'re already at full health!', colors.light_red)
        return 'cancelled'

    message('Your wounds and aches disappear!.', colors.light_violet)
    player.heal(int(player.max_hp/2))


def cast_lightning():
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None: #no enemy found in range
        message('No enemy in range.', colors.red)
        return 'cancelled'

    message('The lightning bolt strikes ' + monster.name + ' for ' + str(int(LIGHTNING_DAMAGE+(player.wis*monster.magic_weak))) + ' damage.', colors.dark_yellow)
    monster.take_damage(int(LIGHTNING_DAMAGE+(player.wis*monster.magic_weak)), message, player, objects)


def cast_confuse():
    message('Left-click an enemy to confuse it, or right-click to cancel.', colors.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None:
        message('Cancelled.', colors.red)
        return 'cancelled'

    monster.old_ai = monster.ai
    monster.ai = ConfusedMonster(monster.old_ai, message)
    monster.ai.owner = monster
    message(monster.name + ' starts stumbling around in a daze.', colors.light_blue)


def cast_fireball():
    message('Left-click a target tile for the fireball, or right-click to cancel.', colors.light_cyan)
    (x, y) = target_tile()
    if x is None:
        message('Cancelled.', colors.light_red)
        return 'cancelled'
    message('The fireball explodes, scorching everything within ' + str(FIREBALL_RADIUS) + ' feet!', colors.orange)

    for obj in objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.blocks:
            message('The ' + obj.name + ' gets burned for ' + str(int(FIREBALL_DAMAGE+(player.wis*obj.magic_weak))) + ' damage!', colors.orange)
            obj.take_damage(int(FIREBALL_DAMAGE+(player.wis*obj.magic_weak)), message, player, objects)


def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1 #start with slightly more than max range

    for obj in objects:
        if obj.blocks and not obj == player and (obj.x, obj.y) in visible_tiles:
            dist = player.distance_to(obj)
            if dist < closest_dist:
                closest_enemy = obj
                closest_dist = dist
    return closest_enemy


def target_tile(max_range=None):
    #return the position of a tile left-clicked in player's FOV (optionally
    #in a range) or (None, None) if right-clicked
    global mouse_coord
    while True:
        tdl.flush()
        clicked = False
        for event in tdl.event.get():
            if event.type == 'MOUSEMOTION':
                mouse_coord = event.cell
            if event.type == 'MOUSEDOWN' and event.button == 'LEFT':
                clicked = True
            elif ((event.type == 'MOUSEDOWN' and event.button == 'RIGHT') or
                  (event.type == 'KEYDOWN' and event.key == 'ESCAPE')):
                return (None, None)
        render_all()

        x = mouse_coord[0]
        y = mouse_coord[1]
        if clicked and mouse_coord in visible_tiles and (max_range is None or player.distance(x, y) <= max_range):
            return mouse_coord


def target_monster(max_range=None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None: #player cancelled
            return None

        for obj in objects:
            if obj.x == x and obj.y == y and obj.blocks and obj != player:
                return obj


def place_item(x, y):

    tier_1_weps = [
        RustySword(x, y),
        BentSpear(x, y),
        ChippedMace(x, y),
        OldWhip(x, y),
        CrackedAxe(x, y)
    ]

    tier_1_armor = [
        Coat(x, y),
        Trousers(x, y),
        PlankShield(x, y, ),
        Hat(x, y),
        LeatherVest(x, y)
    ]

    tier_1_consumables = [
        HealingPotion(x, y, cast_heal),
        LesserHealingPotion(x, y, cast_lesser_heal)
    ]

    tier_1_scrolls = [
        LightningScroll(x, y, cast_lightning),
        ConfuseScroll(x, y, cast_confuse),
        FireballScroll(x, y, cast_fireball)
    ]

    tier_2_weps = [
        Trident(x, y),
        Mournblade(x, y),
        ChainWhip(x, y)
    ]

    tier_2_armor = [
        RedMail(x, y),
        Bucket(x, y),
        PotLid(x, y),
        LeatherVest(x, y),
        PlatedJeans(x, y)
    ]

    item_group = random.choice(['potion', 'armor', 'wep', 'gold', 'scroll'])

    if item_group == 'potion':
        item = random.choice([random.choice(tier_1_consumables)])

    elif item_group == 'armor':
        item = random.choice([random.choice(tier_1_armor)])

    elif item_group == 'wep':
        item = random.choice([random.choice(tier_1_weps)])

    elif item_group == 'gold':
        item = Gold(x, y)

    elif item_group == 'scroll':
        item = random.choice([random.choice(tier_1_scrolls)])

    objects.append(item)
    item.send_to_back(objects)


def new_game():
    global player, inventory, my_map, game_state

    player = Fighter(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, char='@', name='Rogue', color=colors.white, blocks=True,
                     hp=150, xp=50, att=3, wis=2, death_function=player_death)


    my_map = [[Tile(True)
               for y in range(MAP_HEIGHT)]
              for x in range(MAP_WIDTH)]

    make_map()

    game_state = 'playing'
    inventory = []
    consumables = []
    equips = []

    objects.append(player)
    wep = random.choice([
        RustySword(player.x, player.y),
        BentSpear(player.x, player.y),
        ChippedMace(player.x, player.y),
        OldWhip(player.x, player.y),
        CrackedAxe(player.x, player.y)
    ])
    wep.equip(player, message, inventory)
    player.wep = wep

    game_msgs.clear()

    message(player.name + ' has entered Floor 1 of Korum-Zal\'s domain.', colors.red)

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


def play_game():
    global mouse_coord, fov_recompute

    player_action = None
    mouse_coord = (0, 0)
    fov_recompute = True
    con.clear()

    while not tdl.event.is_window_closed():
        render_all()
        tdl.flush()
        for obj in objects:
            obj.clear(root)

        player_action = handle_keys()
        if player_action == 'exit':
            root.clear()
            save_game()
            break

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

        player.check_xp(player, message)
        player.check_limits()

        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in objects:
                if obj.ai:
                    if turns % obj.spd == 0:
                        obj.ai.take_turn(visible_tiles, player, turns, message, my_map, objects)


def main_menu():
    img = image_load("menu_background1.png")
    pygame.mixer.init()
    while not tdl.event.is_window_closed():
        img.blit_2x(root, 0, 0)

        title = 'Pyrl'
        center = (SCREEN_WIDTH-len(title)) // 2
        root.draw_str(center, SCREEN_HEIGHT//2-4, title, bg=None, fg=colors.white)

        title = 'By Nick Hilger'
        center = (SCREEN_WIDTH - len(title)) // 2
        root.draw_str(center, SCREEN_HEIGHT-2, title, bg=None, fg=colors.light_gray)

        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0:
            new_game()
            play_game()
        if choice == 1:  # load last game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()
        elif choice == 2:
            break


def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    with shelve.open('savegame', 'n') as savefile:
        savefile['my_map'] = my_map
        savefile['objects'] = objects
        savefile['player_index'] = objects.index(player)
        savefile['inventory'] = inventory
        # savefile['game_msgs'] = game_msgs
        savefile['game_state'] = game_state
        savefile.close()


def load_game():
    global my_map, objects, player, inventory, game_state
    with shelve.open('savegame', 'r') as savefile:
        my_map = savefile['my_map']
        objects = savefile['objects']
        player = objects[savefile['player_index']]  # get index of player in objects list and access it
        inventory = savefile['inventory']
        # game_msgs = savefile['game_msgs']
        game_state = savefile['game_state']


def msgbox(text, width=50):
    menu(text, [], width)

#######################
#Init and Main Loop   #
#######################


tdl.set_font('Fonts/dejavu_wide16x16_gs_tc.png', greyscale=True, altLayout=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRL", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

tdl.set_fps(30)

main_menu()