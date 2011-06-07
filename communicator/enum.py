from collections import namedtuple

RIGHT,      \
LEFT,       \
UP,         \
DOWN,       \
UP_LEFT,    \
DOWN_RIGHT, \
UP_RIGHT,   \
DOWN_LEFT = range(8)

Connections = namedtuple('Connections', 'right left up down up_left down_right up_right down_left')

class Connections(object):
    def __init__(self, right, left, up, down):
        self.right = right
        self.left = left
        self.up = up
        self.down = down

        self.up_left = None
        self.up_right = None
        self.down_left = None
        self.down_right = None

    def __repr__(self):
        return "right=%s, left=%s, up=%s, down=%s, ul=%s, ur=%s, dl=%s, dr=%s" % \
            (self.right, self.left, self.up, self.down,
             self.up_left, self.up_right, self.down_left, self.down_right)
