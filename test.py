import pygame as pg  # https://pyga.me/docs/
import os

"""
Some motivational words for myself:
This is going to be the best top down shooter in python ever!
This framework is going to be reusable for other 2D games also.
"""

################
# GLOBAL CONST #
################
FPS = 60
DISPLAY_SIZE = (1280, 720)  # use the user setting to define this
NATIVE_RESOLUTION = (320, 180)
HALF_NATIVE_RESOLUTION = (160, 90)
PNG_DIR = "assets/png"
SURFACES_DICT = {}
BACKGROUND_WIDTH = 336
HALF_BACKGROUND_WIDTH = 168
ONE_TILE = 16


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
    SURFACES_DICT[key] = SURFACE


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

def apply_flash_shader(surface, color=(0, 0, 0, 255)):
    """
    Apply a flash shader to given surface by blending it with a given color.
    """
    # copy surface (so does not change original)
    surface_copy = surface.copy()

    # check each pixel, turn non-transparent pixels to given color
    for y in range(surface_copy.get_height()):
        for x in range(surface_copy.get_width()):
            pixel = surface_copy.get_at((x, y))
            # pixel is non-transparent? set color
            if pixel[3] != 0:
                surface_copy.set_at((x, y), color)

    # blit surface copy to output surface
    output_surface = pg.Surface(surface_copy.get_size(), pg.SRCALPHA)
    output_surface.blit(surface_copy, (0, 0))

    return output_surface


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


class Camera(pg.sprite.Sprite):
    """
    A point in space that can follow a target, things are drawn based on camera global position.
    Camera is an illusion where things are drawn in respect to its global position.
    This game camera only move sideways, left limit is always 0. Right limit is always 16 (bg is always 336 wide)
    """
    def __init__(self):
        super().__init__()
        ##############
        # PROPERTIES #
        ##############
        # just so that this counts as a sprite obj, so that it can be added to sprite group (for the updates)
        self.image = None
        self.rect = None

        self.global_position = pg.Vector2(0, 0)
        self.target = None
        self.MOVEMENT_WEIGHT = 0.1
        self.RIGHT_LIMIT = BACKGROUND_WIDTH - NATIVE_RESOLUTION[0]

    ###########
    # METHODS #
    ###########
    def update(self, delta):
        """
        Updates global position to approach target.
        """
        if self.target == None:
            return
        
        # this game camera do not follow vertical movements
        # centered_target_y = self.target.rect.y - HALF_NATIVE_RESOLUTION[1]
        centered_target_x = self.target.rect.x - HALF_NATIVE_RESOLUTION[0]
        
        # this game camera do not follow vertical movements
        # self.global_position.y = lerp(self.global_position.y, centered_target_y, self.MOVEMENT_WEIGHT)
        self.global_position.x = lerp(self.global_position.x, centered_target_x, self.MOVEMENT_WEIGHT)

        # camera limit
        self.global_position.x = max(0, min(self.global_position.x, self.RIGHT_LIMIT))

    ##########
    # SETTER #
    ##########
    def set_target(self, target: any):
        self.target = target
        centered_target_x = self.target.rect.x - HALF_NATIVE_RESOLUTION[0]
        self.global_position.x = centered_target_x


# global class for sprite class to use for drawing
# sprite class is everywhere and they all need the camera
Cam = Camera()


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
        Also for camera = offset where to draw things based on player position
        """
        for spr in self.sprites():
            # get player offset
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
        self.frame_width = surface.get_width() // h_frame
        self.frame_height = surface.get_height() // v_frame

        for col in range(h_frame):
            for row in range(v_frame):
                frame_x = col * self.frame_width
                frame_y = row * self.frame_height
                self.frame_data[len(self.frame_data)] = (frame_x, frame_y, self.frame_width, self.frame_height)
    
    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        Frame property uses the frame data to determine what part of the sprite should it blit to NATIVE_SURFACE.
        """
        # get the sprite from spritesheet
        frame_x, frame_y, frame_width, frame_height = self.frame_data[self.frame]
        frame_rect = pg.Rect(frame_x, frame_y, frame_width, frame_height)

        # global position -> position in respect to camera
        on_camera_rect = pg.Rect(
            self.rect.x - Cam.global_position.x,
            self.rect.y - Cam.global_position.y,
            self.rect.width,
            self.rect.height
        )

        NATIVE_SURFACE.blit(self.image, on_camera_rect, frame_rect)


##########
# ACTORS #
##########
class Background(pg.sprite.Sprite):
    """
    A background sprite.
    """
    def __init__(self):
        super().__init__()
        ##############   
        # PROPERTIES #
        ##############
        self.Sprite = Sprite(surface=SURFACES_DICT["field"], h_frame=1, v_frame=1)
        self.image = self.Sprite.image
        self.rect = self.Sprite.rect

    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        This func is called by parent. 
        Call sprite objects draw functions here.
        """
        self.Sprite.draw()


class BackgroundScroller(pg.sprite.Sprite):
    """
    Scrolls its 2 background children.
    This allows for smooth transitions (change the background children surfaces)
    """
    def __init__(self):
        super().__init__()
        ############
        # CHILDREN #
        ############
        self.BackgroundTop = Background()
        self.BackgroundBottom = Background()

        # position top bg bottom to be at bottom background top
        self.BackgroundTop.rect.y -= self.BackgroundTop.rect.height

    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        This func is called by the Group class. 
        Call sprite objects draw functions here.
        """
        # background top
        self.BackgroundTop.draw()

        # background bottom
        self.BackgroundBottom.draw()
    
    
    def update(self, delta):
        """
        This func is called by the Group class.
        Updates background children position.
        """
        # background top
        self.BackgroundTop.rect.y += 1
        if self.BackgroundTop.rect.y == self.BackgroundTop.rect.height:
            self.BackgroundTop.rect.bottom = 0

        # background bottom
        self.BackgroundBottom.rect.y += 1
        if self.BackgroundBottom.rect.y == self.BackgroundBottom.rect.height:
            self.BackgroundBottom.rect.bottom = 0
    
    # TODO: add change background surface method, and handle smooth surface transition


class PlayerShadow(pg.sprite.Sprite):
    """
    This is always a child of someone. Frame is updated based on parent's. 
    """
    def __init__(self):
        super().__init__()
        ##############   
        # PROPERTIES #
        ##############

        # pre process the surface, turn non transparent pixel to black
        black_sprite_sheet_surface = apply_flash_shader(SURFACES_DICT["player"], color=(0, 0, 0, 255))

        # scale it down by 50%
        # TODO: have this scaling be configurable for animation (take off and landing)
        half_width = black_sprite_sheet_surface.get_width() // 2
        half_height = black_sprite_sheet_surface.get_height() // 2
        scaled_black_sprite_sheet_surface = pg.transform.scale(black_sprite_sheet_surface, (half_width, half_height))

        self.Sprite = Sprite(surface=scaled_black_sprite_sheet_surface, h_frame=11, v_frame=1)
        self.image = self.Sprite.image
        self.rect = self.Sprite.rect

        self.local_position = pg.Vector2(0, 0)

    ###########
    # METHODS #
    ###########
    def draw(self):
        """
        This func is called by the parent.
        """
        self.Sprite.draw()
    
    def update(self, delta, parent_rect, parent_sprite_frame_index):
        """
        This func is called by the parent.
        Updates position and my Sprite frame index.
        """
        self.rect.x = parent_rect.x + self.local_position.x
        self.rect.y = parent_rect.y + self.local_position.y
        self.Sprite.frame = parent_sprite_frame_index


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
        self.Sprite = Sprite(surface=SURFACES_DICT["player_exhaust"], h_frame=3, v_frame=1)
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
        This func is called by the parent.
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
        self.Sprite = Sprite(surface=SURFACES_DICT["player"], h_frame=11, v_frame=1)
        self.image = self.Sprite.image
        self.rect = self.Sprite.rect

        # initial sprite frame (5 = no banking)
        self.Sprite.frame = 5

        ############
        # CHILDREN #
        ############
        # exhaust flame
        self.ExhaustFlame = PlayerExhaustFlame()
        self.ExhaustFlame.local_position.y = 15.0
        # shadow
        self.Shadow = PlayerShadow()
        self.Shadow.local_position.y = 15.0
        self.Shadow.local_position.x = 15.0
        # lists (drawing does not need any args)
        self.children = [
            self.ExhaustFlame,
            self.Shadow
        ]

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

        # draw children
        for child in self.children:
            child.draw()
    
    def update(self, delta):
        """
        This func is called by the Group class.
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
        self.Shadow.update(delta, self.rect, self.Sprite.frame)
        
    
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
        # SETUP PLAYER
        self.Player = Player()
        # in this game the player always start like this, bg is wider but has same height as window
        # update player position to middle
        self.Player.rect.topleft = pg.Vector2(HALF_BACKGROUND_WIDTH, HALF_NATIVE_RESOLUTION[1])
        self.Player.rect.top -= self.Player.Sprite.frame_height / 2
        # shift downward by 3 tiles - 1 tile is 16px
        self.Player.rect.top += ONE_TILE * 3

        # background scroller
        self.BackgroundScroller = BackgroundScroller()

        # SETUP CAMERA
        # camera initial target in player
        Cam.set_target(self.Player)
        # no need to update camera limit, this game camera limit is fixed

        # layers (can do quadtree collision AABB!)
        self.DrawnLayer = Group()  # for things that needs to be drawn
        self.UpdateLayer = Group()  # for things that needs to be updated

        # fill draw layers (order matters, top = drawn most bottom)
        self.DrawnLayer.add(self.BackgroundScroller)
        self.DrawnLayer.add(self.Player)

        # fill update layers, anything that needs updating goes here
        self.UpdateLayer.add(self.BackgroundScroller)
        self.UpdateLayer.add(self.Player)
        self.UpdateLayer.add(Cam)
    
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

    # DEBUG
    # draw on viewport, 2 lines in mid horizontal and mid vertical
    # pg.draw.line(NATIVE_SURFACE, "red", (167, 0), (167, 320), 2)
    # pg.draw.line(NATIVE_SURFACE, "red", (0, 90), (335, 90), 2)

    # BLIT NATIVE TO DISPLAY
    SCALED_NATIVE_SURFACE = pg.transform.scale(NATIVE_SURFACE, DISPLAY_SIZE)
    DISPLAY_SURFACE.blit(SCALED_NATIVE_SURFACE, (0, 0))


    # UPDATE DISPLAY SURF TO SCREEN
    pg.display.flip()

pg.quit()
