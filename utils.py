import textwrap
import colors
from config import *

game_msgs = []

def message(new_msg, color=colors.white):
    #split the message into multiple lines, if need be
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        game_msgs.append((line, color))