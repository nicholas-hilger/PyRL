import colors


def monster_death(monster, message, player, objects):
    message(monster.name.capitalize() + ' collapses in a pile of gore.', colors.red)
    monster.char = '%'
    monster.color = colors.crimson
    player.xp += monster.max_xp
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = monster.name + '\'s remains'
    monster.send_to_back(objects)

def player_death(player, message):
    global game_state
    message('You died!', colors.dark_red)
    game_state = 'dead'

    #turn the player into a corpse
    player.char = '%'
    player.color = colors.darker_red