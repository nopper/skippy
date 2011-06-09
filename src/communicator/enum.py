RIGHT,      \
LEFT,       \
UP,         \
DOWN,       \
UP_LEFT,    \
DOWN_RIGHT, \
UP_RIGHT,   \
DOWN_LEFT = range(8)

LABELS = 'right left up down up_left down_right up_right down_left'
RLABELS = 'left right down up down_right up_left down_left up_right'

LABELS = LABELS.split(' ')
RLABELS = RLABELS.split(' ')
ORDERED = range(8)
REVERSED = [LEFT, RIGHT, DOWN, UP, DOWN_RIGHT, UP_LEFT, DOWN_LEFT, UP_RIGHT]

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

    def convert_to_id(self):
        for lbl in LABELS:
            obj = getattr(self, lbl)

            if obj is None:
                setattr(self, lbl, None)
                continue

            wid = obj.wid

            setattr(self, lbl, wid)
