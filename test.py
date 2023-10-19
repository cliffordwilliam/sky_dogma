import pygame as pg  # https://pyga.me/docs/
import os

# const
FPS = 60
DISPLAY_SIZE = (320, 180)
PNG_DIR = "assets/png"
PNG_LIST = []

pg.init()
DISPLAY_SURFACE = pg.display.set_mode(DISPLAY_SIZE)
CLOCK = pg.time.Clock()

is_running = True

##########
# HELPER #
##########

def lerp(start:float, end:float, weight:float):
    out = start + (end - start) * weight
    if abs(out) < 1:
        out = 0
    return out

def Sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


# get all pngs (this game is small)
for filename in os.listdir(PNG_DIR):
    RELATIVE_PATH = os.path.join(PNG_DIR, filename)
    SURFACE = pg.image.load(RELATIVE_PATH)
    PNG_LIST.append(SURFACE)

# make layer obj
class Group(pg.sprite.Group):

    def draw(self):
        """
        Override the default draw method to instead call the actor draw method
        """
        for spr in self.sprites():
            spr.draw()

# layers (can do quadtree collision AABB!)
DrawnLayer = Group()  # anything that needs to be updated & drawn goes here

# building blocks
class Animator:
    def __init__(self):

        ##############   
        # properties #
        ##############

        self.animations = {}
        self.current_animation = None
        self.keyframe_index = 0
        self.elapsed_frame = 0
        self.listeners = {}  # key = event name | val = list of listeners

    ###########    
    # methods #
    ###########

    def add_animation(
            self, 
            name: str, 
            target: any, 
            keyframes: list[tuple[int, any]], 
            property_name: str, 
            is_looping: bool = False
            ) -> None:
        
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
        
        if name in self.animations:
            self.current_animation = name
            self.keyframe_index = 0
            self.elapsed_frame = 0
    
    def connect(
            self,
            event_name: str,
            method,
            ):
        
        # already have some listeners? add more listeners
        if event_name in self.listeners:
            self.listeners[event_name].append(method)
        # no one listening? make new listener
        else:
            self.listeners[event_name] = [method]

    # needs to be called!
    def update(self):
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

        else:
            if is_looping:
                self.keyframe_index = -1
                self.elapsed_frame = -1
            else:
                self.animation_finished()  # fire event

    ##########
    # events #
    ##########

    def animation_finished(self):
        # no listeners? quit
        if not "animation_finished" in self.listeners:
            return
        
        # call the connected functions
        for method in self.listeners["animation_finished"]:
            method(self.current_animation)


class Sprite(pg.sprite.Sprite):
    def __init__(self, surface, h_frame: int, v_frame: int):
        super().__init__()
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
        
    def draw(self):
        frame_x, frame_y, frame_width, frame_height = self.frame_data[self.frame]
        frame_rect = pg.Rect(frame_x, frame_y, frame_width, frame_height)
        DISPLAY_SURFACE.blit(self.image, self.rect, frame_rect)


class Input:
    def __init__(self) -> None:
        self.key_states = {}  # key: event.key | val: bool
    
    def update(self, event):
        # update key states dict
        if event.type == pg.KEYDOWN:
            self.key_states[event.key] = True
        elif event.type == pg.KEYUP:
            self.key_states[event.key] = False
    
    def is_action_pressed(self, key):
        # key = pg.K_DOWN
        return self.key_states.get(key, False)
    
    def is_action_just_pressed(self, key):
        # key = pg.K_DOWN
        return self.is_key_pressed(key) and not self.key_states.get(key, False)

# global class for input queries
Input = Input()


# player
class Player(pg.sprite.Sprite):
    def __init__(self):

        ##############   
        # PROPERTIES #
        ##############

        super().__init__()
        self.sprite = Sprite(surface=PNG_LIST[1], h_frame=5, v_frame=2)
        self.image = self.sprite.image
        self.rect = self.sprite.rect

        # init animations
        self.animator = Animator()
        # idle animation
        self.animator.add_animation(
            name="idle",
            target=self.sprite,
            keyframes=[
                (0, 4),
                (3, 5),
                (6, 4),
            ],
            property_name="frame",
            is_looping=True
        )

        # left banking transition animation
        self.animator.add_animation(
            name="to_left_idle_from_idle",
            target=self.sprite,
            keyframes=[
                (0, 2),
                (3, 3),
            ],
            property_name="frame"
        )

        # left banking idle animation
        self.animator.add_animation(
            name="left_idle",
            target=self.sprite,
            keyframes=[
                (0, 0),
                (3, 1),
                (6, 0),
            ],
            property_name="frame",
            is_looping=True
        )

        # right banking transition animation
        self.animator.add_animation(
            name="to_right_idle_from_idle",
            target=self.sprite,
            keyframes=[
                (0, 6),
                (3, 7),
            ],
            property_name="frame"
        )

        # right banking idle animation
        self.animator.add_animation(
            name="right_idle",
            target=self.sprite,
            keyframes=[
                (0, 8),
                (3, 9),
                (6, 8),
            ],
            property_name="frame",
            is_looping=True
        )

        # connect animation finished signal
        self.animator.connect("animation_finished", self.on_animator_animation_finished)

        # state - start at 0
        self.set_state(0)

        # movement
        self.velocity = pg.math.Vector2(0, 0)
        self.MAX_VELOCITY = 90.0  # px / s
        self.MOVEMENT_WEIGHT = 0.1
        self.remainder_x = 0
        self.remainder_y = 0

    #############
    # CALLBACKS #
    #############

    # handle transition animations
    def on_animator_animation_finished(self, animation_name):
        if animation_name == "to_left_idle_from_idle":
            self.animator.play("left_idle")
        elif animation_name == "to_right_idle_from_idle":
            self.animator.play("right_idle")

    def draw(self):
        self.sprite.draw()
    
    def update(self, delta):
        self.animator.update()

        direction = pg.math.Vector2(
            Input.is_action_pressed(pg.K_RIGHT) - Input.is_action_pressed(pg.K_LEFT), 
            Input.is_action_pressed(pg.K_DOWN) - Input.is_action_pressed(pg.K_UP)
        )
        if direction.x or direction.y:
            direction.normalize()

        ##########
        # STATES #
        ##########

        # idle
        if self.state == 0:
            # ACTION
            # acc / decel horizontally
            self.velocity.y = lerp(self.velocity.y, self.MAX_VELOCITY * direction.y, self.MOVEMENT_WEIGHT)
            # acc / decel vertically
            self.velocity.x = lerp(self.velocity.x, self.MAX_VELOCITY * direction.x, self.MOVEMENT_WEIGHT)
            if self.velocity.x or self.velocity.y:
                self.velocity.normalize()
            
            # update position (https://www.reddit.com/r/pygame/comments/q8whz6/why_is_my_movement_faster_in_some_directions_then/)
            self.move_x(self.velocity.x * delta)
            self.move_y(self.velocity.y * delta)

            # EXIT
            # to idle left
            if direction[0] == -1:
                self.set_state(1)
            # to idle right
            elif direction[0] == 1:
                self.set_state(2)

        # left
        elif self.state == 1:
            # ACTION
            # acc / decel horizontally
            self.velocity.y = lerp(self.velocity.y, self.MAX_VELOCITY * direction.y, self.MOVEMENT_WEIGHT)
            # acc / decel vertically
            self.velocity.x = lerp(self.velocity.x, self.MAX_VELOCITY * direction.x, self.MOVEMENT_WEIGHT)
            if self.velocity.x or self.velocity.y:
                self.velocity.normalize()
            
            # update position (https://www.reddit.com/r/pygame/comments/q8whz6/why_is_my_movement_faster_in_some_directions_then/)
            self.move_x(self.velocity.x * delta)
            self.move_y(self.velocity.y * delta)

            # move left
            # EXIT
            # to idle
            if not direction[0]:
                self.set_state(0)
            # to idle right
            elif direction[0] == 1:
                self.set_state(2)

        # right
        elif self.state == 2:
            # ACTION
            # acc / decel horizontally
            self.velocity.y = lerp(self.velocity.y, self.MAX_VELOCITY * direction.y, self.MOVEMENT_WEIGHT)
            # acc / decel vertically
            self.velocity.x = lerp(self.velocity.x, self.MAX_VELOCITY * direction.x, self.MOVEMENT_WEIGHT)
            if self.velocity.x or self.velocity.y:
                self.velocity.normalize()
            
            # update position (https://www.reddit.com/r/pygame/comments/q8whz6/why_is_my_movement_faster_in_some_directions_then/)
            self.move_x(self.velocity.x * delta)
            self.move_y(self.velocity.y * delta)


            # move right
            # EXIT
            # to idle
            if not direction[0]:
                self.set_state(0)
            # to idle left
            elif direction[0] == -1:
                self.set_state(1)
    
    ##########
    # HELPER #
    ##########

    # https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5
    def move_x(self, amount: float):
        self.remainder_x += amount
        move = round(self.remainder_x)

        if move == 0:
            return
        
        self.remainder_x -= move
        sign = Sign(move)

        while move != 0:
            # check collision here, break if collided
            self.rect.x += sign
            move -= sign

    # https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5
    def move_y(self, amount: float):
        self.remainder_y += amount
        move = round(self.remainder_y)

        if move == 0:
            return
        
        self.remainder_y -= move
        sign = Sign(move)

        while move != 0:
            # check collision here, break if collided
            self.rect.y += sign
            move -= sign
    

    ##########
    # GETTER #
    ##########

    def set_state(self, value):
        old_state = value
        self.state = value

        ########
        # EXIT #
        ########

        # from idle
        if old_state == 0:
            pass
        
        # from left
        if old_state == 1:
            pass
        
        # from right
        if old_state == 2:
            pass
        
        #########
        # ENTER #
        #########
        
        # to idle
        if self.state == 0:
            self.animator.play("idle")

        # to left
        if self.state == 1:
            self.animator.play("to_left_idle_from_idle")

        # to right
        if self.state == 2:
            self.animator.play("to_right_idle_from_idle")


# player
player = Player()
DrawnLayer.add(player)

#############
# MAIN LOOP #
#############

while is_running:
    # 60 FPS LIMIT
    delta = CLOCK.tick(FPS) / 1000

    # EVENTS
    for event in pg.event.get():
        # check window x button clicked
        if event.type == pg.QUIT:
            is_running = False
        # update manager
        Input.update(event)
    
    # CLEAR
    DISPLAY_SURFACE.fill("black")

    # UPDATE
    DrawnLayer.update(delta)

    # DRAW
    DrawnLayer.draw()

    # UPDATE DISPLAY SURF TO SCREEN
    pg.display.flip()

pg.quit()
