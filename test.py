import pygame as pg  # https://pyga.me/docs/
import os

################
# GLOBAL CONST #
################
FPS = 60
DISPLAY_SIZE = (1280, 720)  # use the user setting to define this
NATIVE_RESOLUTION = (320, 180)
PNG_DIR = "assets/png"
PNG_DICT = {}

###########
# PG INIT #
###########
pg.init()
DISPLAY_SURFACE = pg.display.set_mode(DISPLAY_SIZE)
CLOCK = pg.time.Clock()

is_running = True

##########
# CANVAS #
##########
# BLIT HERE, THEN BLIT THIS TO DISPLAY_SURFACE
NATIVE_SURFACE = pg.Surface(NATIVE_RESOLUTION)


################
# PNG -> SURFS #
################
for filename in os.listdir(PNG_DIR):
    # Get all pngs (this game is small)
    RELATIVE_PATH = os.path.join(PNG_DIR, filename)
    SURFACE = pg.image.load(RELATIVE_PATH)

    # key = filename (without extension) | val = surface
    key = os.path.splitext(filename)[0]
    PNG_DICT[key] = SURFACE


##########
# HELPER #
##########
def lerp(start: float, end: float, weight: float):
    """
    Linear interpolation.
    """
    out = start + (end - start) * weight
    if abs(out) < 1:
        out = 0
    return out

def Sign(value):
    """
    Return value sign.
    """
    if value > 0:
        return 1
    elif value < 0:
        return -1
    else:
        return 0

########
# MISC #
########
class Input:
    """
    For all Input queries necessity.
    """
    def __init__(self):
        ##############
        # PROPERTIES #
        ##############
        self.key_states = {}  # key: event.key | val: bool
    
    ###########
    # METHODS #
    ###########
    def update(self, event):
        """
        Update the key_states dict with given event.
        """
        if event.type == pg.KEYDOWN:
            self.key_states[event.key] = True
        elif event.type == pg.KEYUP:
            self.key_states[event.key] = False
    
    def is_action_pressed(self, key):
        """
        Return bool for held given key, expects key = pg.K_DOWN.
        """
        return self.key_states.get(key, False)
    
    def is_action_just_pressed(self, key):
        """
        Return bool for given key change state from not pressed to pressed, expects key = pg.K_DOWN.
        """
        return self.is_key_pressed(key) and not self.key_states.get(key, False)


# global class for input queries
Input = Input()


# for rendering & collision
class Group(pg.sprite.Group):
    """
    Can act both as rendering and collision layer. Add entities in here.
    """
    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        Override the default draw method to instead call the actor draw method, 
        actor draw method needs the frame index data to draw certain section of their spritesheet.
        """
        for spr in self.sprites():
            spr.draw()

#########
# NODES #
#########
class Animator:
    """
    Able to change given target properties, following given keyframes data = list of tuples.
    """
    def __init__(self):
        ##############
        # PROPERTIES #
        ##############
        self.animations = {}
        self.current_animation = None
        self.keyframe_index = 0
        self.elapsed_frame = 0
        self.listeners = {}  # key = event name | val = list of listeners

    ###########
    # METHODS #
    ###########
    def add_animation(
            self, 
            name: str, 
            target: any, 
            keyframes: list[tuple[int, any]], 
            property_name: str, 
            is_looping: bool = False
            ):
        """
        Expects keyframes = [(frame, value)]. Value of given property.
        """
        
        self.animations[name] = {
            'target': target, 
            'keyframes': keyframes, 
            'property_name': property_name,
            'is_looping': is_looping
        }
    
    def play(
            self, 
            name: str
            ):
        """
        Updates current_animation.
        """
        
        if name in self.animations:
            self.current_animation = name
    
    def connect(
            self,
            event_name: str,
            method,
            ):
        """
        Pass in what you want to listen and the callback to be invoked.
        """
        
        # already have some listeners? add more listeners
        if event_name in self.listeners:
            self.listeners[event_name].append(method)
        # no one listening? make new listener
        else:
            self.listeners[event_name] = [method]

    # needs to be called!
    def update(self):
        """
        Needs to be called, updates the elapsed_frame. Which is used to set attribute and make events happen.
        """

        # no current animation? return
        if not self.current_animation:
            return
        
        # get data of current animation
        anim = self.animations[self.current_animation]
        target = anim['target']
        keyframes = anim['keyframes']
        property_name = anim['property_name']
        is_looping = anim['is_looping']
    
        # udapte elapsed frame
        self.elapsed_frame += 1

        # keyframe index now is still not last?
        if self.keyframe_index < len(keyframes) - 1:
            # elapsed_frame now is == next keyframe frame item?
            if self.elapsed_frame == keyframes[self.keyframe_index + 1][0]:
                self.keyframe_index += 1
                # TODO: have a callback check here (play sound at frame 5)
                setattr(target, property_name, keyframes[self.keyframe_index][1])

        # keyframe at last index?
        else:
            # looping? reset to 1st frame, reset elapsed frame counter too
            if is_looping:
                self.keyframe_index = -1
                self.elapsed_frame = -1
            # not looping? animation_finished event happens now
            else:
                self.animation_finished()  # fire event

    ##########
    # EVENTS #
    ##########
    def animation_finished(self):
        """
        Happens when any animation is finished (not looping ones only).
        """
        # no listeners? return
        if not "animation_finished" in self.listeners:
            return
        
        # call the connected functions
        for method in self.listeners["animation_finished"]:
            method(self.current_animation)


class Sprite(pg.sprite.Sprite):
    """
    Takes a spritesheet and uses it to create a frame data.
    Change the frame property to change which sprite is drawn.
    """
    def __init__(self, surface, h_frame: int, v_frame: int):
        super().__init__()
        ##############
        # PROPERTIES #
        ##############
        self.image = surface
        self.rect = surface.get_rect()
        self.frame = 0
        self.frame_data = {}

        # set frame data
        frame_width = surface.get_width() // h_frame
        frame_height = surface.get_height() // v_frame

        for col in range(h_frame):
            for row in range(v_frame):
                frame_x = col * frame_width
                frame_y = row * frame_height
                self.frame_data[len(self.frame_data)] = (frame_x, frame_y, frame_width, frame_height)
    
    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        Frame property uses the frame data to determine what part of the sprite should it blit to NATIVE_SURFACE.
        """
        frame_x, frame_y, frame_width, frame_height = self.frame_data[self.frame]
        frame_rect = pg.Rect(frame_x, frame_y, frame_width, frame_height)
        NATIVE_SURFACE.blit(self.image, self.rect, frame_rect)


##########
# ACTORS #
##########
class PlayerExhaustFlame(pg.sprite.Sprite):
    """
    This is always a child of someone. Autoplays its burning animation. 
    (Maybe has other anim in future).
    """
    def __init__(self):
        super().__init__()
        ##############   
        # PROPERTIES #
        ##############
        self.Sprite = Sprite(surface=PNG_DICT["player_exhaust"], h_frame=3, v_frame=1)
        self.image = self.Sprite.image
        self.rect = self.Sprite.rect

        self.local_position = pg.Vector2(0, 0)

        # animation
        self.animator = Animator()
        self.animator.add_animation(
            name="default",
            target=self.Sprite,
             keyframes=[
                 (0, 0),
                 (2, 1),
                 (4, 2),
                 (6, 0),
             ],
            property_name="frame",
             is_looping=True
        )
        self.animator.play("default")

    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        This func is called by the parent.
        """
        self.Sprite.draw()
    
    def update(self, delta, parent_rect):
        """
        Updates animation and position.
        """
        self.animator.update()
        self.rect.x = parent_rect.x + self.local_position.x
        self.rect.y = parent_rect.y + self.local_position.y


class Player(pg.sprite.Sprite):
    """
    Listens to user input and updates it's position.
    Has Sprite that is updated based on it's velocity.x
    """
    def __init__(self):
        super().__init__()
        ##############   
        # PROPERTIES #
        ##############
        self.Sprite = Sprite(surface=PNG_DICT["player"], h_frame=11, v_frame=1)
        self.image = self.Sprite.image
        self.rect = self.Sprite.rect

        # initial sprite frame (5 = no banking)
        self.Sprite.frame = 5

        # children (create a list to iter each children later)
        self.ExhaustFlame = PlayerExhaustFlame()
        self.ExhaustFlame.local_position.y = 15.0

        # movement
        self.MAX_VELOCITY = 90.0  # px / s
        self.MOVEMENT_WEIGHT = 0.1
        self.velocity = pg.math.Vector2(0, 0)
        self.remainder = pg.math.Vector2(0, 0)

    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        This func is called by the Group class. 
        Call sprite objects draw functions here.
        """
        self.Sprite.draw()
    
    def update(self, delta):
        """
        Updates anything here based on user input / other actor influences.
        """
        # direction
        direction = pg.math.Vector2(
            Input.is_action_pressed(pg.K_RIGHT) - Input.is_action_pressed(pg.K_LEFT), 
            Input.is_action_pressed(pg.K_DOWN) - Input.is_action_pressed(pg.K_UP)
        )
        if direction.x or direction.y:
            direction.normalize()

        # update velocity with direction
        self.velocity.y = lerp(self.velocity.y, self.MAX_VELOCITY * direction.y, self.MOVEMENT_WEIGHT)
        self.velocity.x = lerp(self.velocity.x, self.MAX_VELOCITY * direction.x, self.MOVEMENT_WEIGHT)
        if self.velocity.x or self.velocity.y:
            self.velocity.normalize()

        # update frame index with velocity (100% to 5%, then shift by 5 frames)
        self.Sprite.frame = int((self.velocity.x / self.MAX_VELOCITY * 100.0) / 17.0) + 5
        
        # update position with velocity
        # https://www.reddit.com/r/pygame/comments/q8whz6/why_is_my_movement_faster_in_some_directions_then/
        self.move_x(self.velocity.x * delta)
        self.move_y(self.velocity.y * delta)

        # update children (position, animation, etc)
        self.ExhaustFlame.update(delta, self.rect)
    
    ##########
    # HELPER #
    ##########
    # https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5
    def move_x(self, amount: float):
        """
        Position updates with int, so collect the lost decimals and adds it to distance to be covered.
        """
        self.remainder.x += amount
        move = round(self.remainder.x)

        if move == 0:
            return
        
        self.remainder.x -= move
        sign = Sign(move)

        while move != 0:
            # check collision here, break if collided
            self.rect.x += sign
            move -= sign

    # https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5
    def move_y(self, amount: float):
        """
        Position updates with int, so collect the lost decimals and adds it to distance to be covered.
        """
        self.remainder.y += amount
        move = round(self.remainder.y)

        if move == 0:
            return
        
        self.remainder.y -= move
        sign = Sign(move)

        while move != 0:
            # check collision here, break if collided
            self.rect.y += sign
            move -= sign

##########
# SCENES #
##########
class Test:
    """
    Testing scene only.
    """
    def __init__(self):
        ############
        # CHILDREN #
        ############
        self.Player = Player()

        # layers (can do quadtree collision AABB!)
        self.DrawnLayer = Group()  # for things that needs to be drawn
        self.UpdateLayer = Group()  # for things that needs to be updated

        # fill layers (order matters, top = drawn most bottom)
        self.DrawnLayer.add(self.Player.ExhaustFlame)
        self.DrawnLayer.add(self.Player)
        self.UpdateLayer.add(self.Player)
    
    ###########
    # METHODS #
    ###########
    def update(self, delta):
        """
        UpdateLayer call its members update func.
        """
        self.UpdateLayer.update(delta)
    
    def draw(self):
        """
        DrawnLayers call its members update func. Order matters
        """
        self.DrawnLayer.draw()

# create scenes
scene = Test()

#############
# MAIN LOOP #
#############
while is_running:
    # 60 FPS LIMIT
    delta = CLOCK.tick(FPS) / 1000.0

    # EVENTS
    for event in pg.event.get():
        # check window x button clicked
        if event.type == pg.QUIT:
            is_running = False
        # update manager
        Input.update(event)
    
    # CLEAR
    NATIVE_SURFACE.fill("blue4")

    # UPDATE
    scene.update(delta)

    # DRAW
    scene.draw()

    # BLIT NATIVE TO DISPLAY
    SCALED_NATIVE_SURFACE = pg.transform.scale(NATIVE_SURFACE, DISPLAY_SIZE)
    DISPLAY_SURFACE.blit(SCALED_NATIVE_SURFACE, (0, 0))


    # UPDATE DISPLAY SURF TO SCREEN
    pg.display.flip()

pg.quit()
