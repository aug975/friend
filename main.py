import pygame
import random
import sys
import pyttsx3
import tempfile
import os
import numpy as np
import pygame.sndarray

from ui_text import text_surface as text_surface_with_font, SpeechBubble, FadingText, ScoreCounter, draw_end_message, WHITE, BLACK
from BottomPanel import BottomPanel
from HealthBar import HealthBar

# potential api i could use for this
# https://www.wordsapi.com/

# start pygame
pygame.init()

# setup pygame mixer
pygame.mixer.init()

def apply_pitch_and_speed(sound: pygame.mixer.Sound, pitch_shift=0.0, speed_change=1.0):
    arr = pygame.sndarray.array(sound).astype(np.float32)

    # Resample for speed + pitch
    factor = speed_change * (2 ** (pitch_shift / 12.0))
    old_len = arr.shape[0] # Unresolved attribute reference 'shape' for class 'ndarray' ??
    new_len = int(old_len / factor)

    # Avoid crash if invalid size
    if new_len < 1:
        return sound

    # Resample using numpy interpolation
    idxs = np.linspace(0, old_len - 1, new_len)
    resampled = np.zeros((new_len, arr.shape[1]), dtype=np.float32)
    for ch in range(arr.shape[1]):
        resampled[:, ch] = np.interp(idxs, np.arange(old_len), arr[:, ch])

    resampled = np.clip(resampled, -32768, 32767).astype(np.int16)  # Unresolved attribute reference 'astype' for class 'ndarray' ????? I think PyCharm is just kinda dumb

    return pygame.mixer.Sound(resampled)

def play_music_random_start(path, loop=-1, volume=0.5):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)

    # length in seconds (works for most formats)
    length = pygame.mixer.Sound(path).get_length()

    # pick random start point (leave 10s margin so it doesn't end instantly)
    start_time = random.uniform(0, max(0, round(length - 10)))

    # play from that offset
    pygame.mixer.music.play(loop, start=start_time)


def _tts_generate(word: str):
    engine = pyttsx3.init()

    base_rate = 175
    rate_variation = random.randint(-30, 30)

    engine.setProperty("voice", engine.getProperty("voices")[1].id)
    engine.setProperty("rate", base_rate + rate_variation)
    engine.setProperty("volume", 1.0)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    engine.save_to_file(word, path)
    engine.runAndWait()
    engine.stop()

    return path


def speak_word(word):
    path = _tts_generate(word)
    base_sound = pygame.mixer.Sound(path)

    # Random pitch between -2 and +2 semitones
    pitch = random.uniform(-2, 4)
    # Random speed between 0.9x and 1.1x
    speed = random.uniform(0.9, 1.1)

    sound = apply_pitch_and_speed(base_sound, pitch_shift=pitch, speed_change=speed)
    sound.play()

# window
# on my last version I HAD THE WIDTH AND HEIGHT BACKWARDS ;w;
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# lazy solution
def run_once_per_text(f):
    printed_texts = set()
    def wrapper(text: str, *args, **kwargs):
        if text not in printed_texts:
            printed_texts.add(text)
            return f(text, *args, **kwargs)
    def _reset():
        printed_texts.clear()
    wrapper.reset = _reset
    return wrapper
@run_once_per_text
def print_once(text:str):
    print(text)

# my old tree was inefficient :(
# loads all the words in a file as a dictionary
# this version is half set (for O1 comparison) and half dict (for O1* random)
class WordDictionary:
    def __init__(self, filename):
        with open(filename) as f:
            gwords = [line.strip().lower() for line in f]

        self.words = gwords  # for random.choice
        self.word_set = set(gwords)  # for O(1) existence checks

    # pick a random word from the dict
    def random_word(self):
        if DEBUG:
            print("BASE: Picking random real word!")  # DEBUG print
        return random.choice(self.words)

    # check if parameter word is in the dict
    def exists(self, word):
        return word.lower() in self.word_set

# creates our dictionary
# awesome naming convention
words = WordDictionary('./resources/words_alpha.txt')

# creates a fake word
def generate_word():
    prefixes = [
        "ab", "ac", "ad", "af", "al", "am", "an", "ap", "ar", "as", "at",
        "bel", "con", "cor", "de", "dis", "ex", "im", "in", "inter",
        "mis", "non", "per", "pre", "pro", "re", "sub", "trans", "un"
    ]

    roots = [
        "tract", "vent", "press", "form", "graph", "lum", "phon",
        "spect", "scrib", "ject", "pel", "vers", "dict", "struct",
        "mov", "serv", "act", "plic", "clus", "cred", "cap", "voc",
        "gen", "port", "ten", "val", "fer", "grad"
    ]

    suffixes = [
        "ment", "ness", "tion", "sion", "dom", "hood", "ship", "ity",
        "ate", "ify", "ize", "en", "ous", "ive", "al", "ic", "ary",
        "ful", "less", "ance", "ence", "able", "ible"
    ]

    # check if it doesn't exist
    while True:
        easter_egg = random.randint(1,100000)
        if easter_egg == 13:
            word = 'koji'
        elif easter_egg == 80:
            word = 'lainwire'
        else:
            word = random.choice(prefixes) + random.choice(roots) + random.choice(suffixes)
        if not words.exists(word):
            if DEBUG:
                print("BASE: Picking random fake word!")  # DEBUG print
            break
        if DEBUG:
            print("Oh! I tried to invent " + word + " but it already exists! Trying again..")  # DEBUG print

    return word

# global variables
# alright listen up:
'''
MOOD is the global variable for friend's mood. 
tells us how she's feeling, for sprite changes and more.
TALKING is the boolean for if friend is giving us a word.
makes it so answer buttons show up, and enables interaction.
REAL is the boolean for if the current word is a real english word.
this determines if the answers will be right or wrong.
SCALE is the float for the friend's sprite scale.
we can easily resize friend with this.
START_EMOTE is a timer check for when friend is showing her mood.
GAME_OVER is a boolean for if the player lost.
that way we can render the ending stuff if it's true, and prevent other stuff from happening.
'''
MOOD = 0
TALKING = False
REAL = True
SCALE = 1.5
START_EMOTE = 0
GAME_OVER = False
DEFAULT_FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48)
BIGGER_FONT = pygame.font.SysFont(None, 72)
SMALL_FONT = pygame.font.SysFont(None, 24)

# easy to toggle debug setting
DEBUG = False

# read the current highscore from the file
file = open("./resources/highscore.txt", "r")
HIGHSCORE = int(file.read())
file.close()

# TODO put the highscore in a file that isn't so easy to edit..?

# these events fire when a word is picked
def chose_real_word(word: str):
    global REAL
    if DEBUG:
        print("Friend picked the REAL word: " + word)  # DEBUG print
    REAL = True

def chose_fake_word(word: str):
    global REAL
    if DEBUG:
        print("Friend picked the FAKE word: " + word)  # DEBUG print
    REAL = False

# initial setup (just the clock for now)
clock = pygame.time.Clock()

# load images and make them have transparency
friendNeutral = pygame.image.load('./resources/friend_neutral.png').convert_alpha()
friendTalk = pygame.image.load('./resources/friend_talk.png').convert_alpha()
friendHappy = pygame.image.load('./resources/friend_happy.png').convert_alpha()
friendSad = pygame.image.load('./resources/friend_sad.png').convert_alpha()
finger_img = pygame.image.load("./resources/finger.png").convert_alpha()

# resize the images with the SCALE global variable
friendNeutral = pygame.transform.scale(friendNeutral,
                                       (friendNeutral.get_size()[0] * SCALE, friendNeutral.get_size()[1] * SCALE))
friendTalk = pygame.transform.scale(friendTalk, (friendTalk.get_size()[0] * SCALE, friendTalk.get_size()[1] * SCALE))
friendHappy = pygame.transform.scale(friendHappy,
                                     (friendHappy.get_size()[0] * SCALE, friendHappy.get_size()[1] * SCALE))
friendSad = pygame.transform.scale(friendSad, (friendSad.get_size()[0] * SCALE, friendSad.get_size()[1] * SCALE))

finger_img = pygame.transform.scale(finger_img,
                                       (finger_img.get_size()[0] * 2, finger_img.get_size()[1] * 2))

# button sprite class
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, active, text="", font=pygame.font.SysFont(None, 28),
                 normal_color=(182, 218, 206), hover_color=(140, 166, 157),
                 inactive_color=(120, 140, 130), border=4, border_color=(0, 0, 0),
                 radius=8, shadow_strength=120, shadow_height_ratio=0.3, finger=None):
        super().__init__()
        self.active = active
        self.font = font
        self.text = text
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.inactive_color = inactive_color
        self.border = border
        self.border_color = border_color
        self.radius = radius
        self.finger = finger

        # finger animation state
        self.finger_visible = False
        self.finger_y = -90  # start offset (appears higher up)
        self.finger_target_y = -300
        self.finger_speed = 1200  # px/sec easing speed

        self.shadow_strength = shadow_strength
        self.shadow_height_ratio = shadow_height_ratio

        text_surf = text_surface_with_font(self.font, self.text, BLACK)
        text_size = text_surf.get_size()
        w, h = text_size[0] * 2, text_size[1] * 2

        self.image = pygame.Surface((w, h + 15), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def _draw_shadow_gradient(self, target):
        """Draw a vertical shadow gradient clipped to the button's rounded shape."""
        w, h = target.get_size()
        gradient_height = int(h * self.shadow_height_ratio)

        # make the gradient
        grad = pygame.Surface((w, gradient_height), pygame.SRCALPHA)
        for y in range(gradient_height):
            alpha = int(self.shadow_strength * (1 - y / gradient_height))
            pygame.draw.line(grad, (0, 0, 0, alpha), (0, y), (w, y))

        # create mask surface with rounded rect (fully opaque inside shape)
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=self.radius)

        # blit gradient into a temp surface same size as button
        temp = pygame.Surface((w, h), pygame.SRCALPHA)
        temp.blit(grad, (0, 0))

        # apply mask
        temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # finally draw onto target
        target.blit(temp, (0, 0))

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        if self.active and self.rect.collidepoint(mouse_pos):
            if not self.finger_visible:
                self.finger_visible = True
                self.finger_y = -360  # reset animation each time
            # ease finger toward target
            if self.finger_y < self.finger_target_y:
                self.finger_y += self.finger_speed * dt
                if self.finger_y > self.finger_target_y:
                    self.finger_y = self.finger_target_y
        else:
            self.finger_visible = False

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()

        # choose base color
        if self.active:
            if self.rect.collidepoint(mouse_pos):
                color = self.hover_color
            else:
                color = self.normal_color
        else:
            color = self.inactive_color

        self.image.fill((0, 0, 0, 0))

        # background
        pygame.draw.rect(self.image, color, self.image.get_rect(),
                         border_radius=self.radius)

        # shadow gradient (before border, under text)
        self._draw_shadow_gradient(self.image)

        # border
        if self.border > 0:
            pygame.draw.rect(self.image, self.border_color, self.image.get_rect(),
                             self.border, border_radius=self.radius)

        # text
        text_surf = text_surface_with_font(self.font, self.text, BLACK)
        text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surf, text_rect)

        screen.blit(self.image, self.rect)

        # draw finger
        if self.finger_visible and self.finger:
            # anchor the finger’s bottom to just above the button
            fx = self.rect.centerx + 160 - self.finger.get_width() // 2
            fy = self.rect.top + self.finger_y
            screen.blit(self.finger, (fx, fy))


# simple sprite
class StaticSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, pos, *groups):
        super().__init__(*groups)
        self.base_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)
        self.visible = True

    def set_visible(self, visible: bool):
        self.visible = visible
        self.image = self.base_image if visible else pygame.Surface((0, 0), pygame.SRCALPHA)

    def update(self):
        # nothing
        pass

bubblegroup = pygame.sprite.Group()

# friend sprite class
class Friend(pygame.sprite.Sprite):
    # friend starts neutral, with no text
    def __init__(self, group):
        pygame.sprite.Sprite.__init__(self)
        self.image = friendNeutral
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 100)
        self.bubble = None
        super().__init__(group)

    def update(self):
        # change sprite to reflect friend's mood
        # x, y = self.rect.center
        if MOOD == 0:
            self.image = friendNeutral
        elif MOOD == 1:
            self.image = friendTalk
        elif MOOD == 2:
            self.image = friendHappy
        elif MOOD == 3:
            self.image = friendSad
        else:
            self.image = friendNeutral

    # function for when friend talks
    def talk(self):
        global MOOD, TALKING
        TALKING = True
        # choose between a real word, or a fake word
        if random.choice([True, False]):
            talk_choice = words.random_word()
            chose_real_word(talk_choice)
        else:
            talk_choice = generate_word()
            chose_fake_word(talk_choice)
        # say that word in a speech bubble
        self.bubble = SpeechBubble(talk_choice, pos=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50), friend_pos=self.rect.center)
        speak_word(talk_choice)

    # get happy if the player gets it right
    def answer_correct(self):
        global MOOD
        self.bubble = None
        MOOD = 2

    # get sad if the player gets it wrong
    def answer_incorrect(self):
        global MOOD
        self.bubble = None
        MOOD = 3

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.bubble:
            self.bubble.draw(screen)

class ParallaxBackground(pygame.sprite.Sprite):
    def __init__(self, screen_rect, image_path, scroll_speed=(20, 20)):
        super().__init__()
        self.width, self.height = screen_rect.size

        # Load texture and convert
        self.texture = pygame.image.load(image_path).convert()
        self.tex_w, self.tex_h = self.texture.get_size()

        # Offset for scrolling
        self.offset = [0.0, 0.0]
        self.scroll_speed = scroll_speed

        # Final surface that fills screen
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft=(0, 0))

    def set_image(self, image_path):
        """Swap background image at runtime (menu, game, game over)."""
        self.texture = pygame.image.load(image_path).convert()
        self.tex_w, self.tex_h = self.texture.get_size()

    def update(self, dt):
        # Move offset
        self.offset[0] = (self.offset[0] + self.scroll_speed[0] * dt) % self.tex_w
        self.offset[1] = (self.offset[1] + self.scroll_speed[1] * dt) % self.tex_h

        self.image.fill((0, 0, 0))  # clear
        ox, oy = int(self.offset[0]), int(self.offset[1])

        # Tile texture across screen
        for x in range(-ox, self.width, self.tex_w):
            for y in range(-oy, self.height, self.tex_h):
                self.image.blit(self.texture, (x, y))

screen_rect = screen.get_rect()
background = ParallaxBackground(screen_rect, "./resources/background.png", scroll_speed=(10, 5))

# game loop
def game_loop():
    global MOOD, TALKING, START_EMOTE, GAME_OVER, HIGHSCORE
    print("Hello! Loading..")
    # sprite groups
    friend_group = pygame.sprite.GroupSingle()
    room_stuff = pygame.sprite.Group()
    ui_group = pygame.sprite.Group()
    ui_health = pygame.sprite.Group()
    ui_panel = pygame.sprite.Group()
    ui_ending = pygame.sprite.Group()
    bg_group = pygame.sprite.Group()
    bg_group.add(background)

    # game isn't over if it just started!!
    GAME_OVER = False
    # main loop boolean
    print("Starting game..")
    running = True
    # friend add friend
    friend = Friend(friend_group)
    StaticSprite('./resources/table.png',(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 295),room_stuff)

    # the panel!!
    panel = BottomPanel(
        screen.get_rect(),
        height=80,
        checker_alpha=30,
        scroll_speed=(20,20),
        groups=(ui_panel,)
    )

    # all the fading texts are here
    texts = []
    # define the buttons
    confirm_button = Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 200, True, "Real", finger=finger_img)
    deny_button = Button(SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT // 2 + 200, True, "Fake", normal_color=(235, 166, 170),hover_color=(184, 137, 139), inactive_color=(184, 137, 139), finger=finger_img)
    restart_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200, True, "Retry", finger=finger_img)
    # define counters
    score = ScoreCounter(pos=(SCREEN_WIDTH // 2, 10), color=(255, 255, 255), groups=(ui_group,))
    ScoreCounter(pos=(SCREEN_WIDTH // 2, 50), color=(190, 190, 190), text="High Score: ", high=True,
                 groups=(ui_group,), font=SMALL_FONT)
    ScoreCounter(pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), color=(255, 255, 255),
                 text="High Score: ", high=True, groups=(ui_ending,),font=BIG_FONT)
    health = HealthBar(20, 20, max_health=3, fg_pattern='./resources/hearts.png', bg_pattern='./resources/damage.png',group=ui_health)

    # friend starts talking right away
    friend.talk()
    # Play in a loop
    play_music_random_start("resources/MS.mp3")

    while running:
        dt = clock.tick(60) / 1000.0
        # game over if the health runs out
        if health.current_health <= 0:
            GAME_OVER = True
        for event in pygame.event.get():
            # handle window closing
            if event.type == pygame.QUIT:
                print("Player wants to exit. Closing...")
                sys.exit()
            # handle key presses
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d and DEBUG:
                    GAME_OVER = True  # DEBUG Force game over
            # handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # when we click on Real
                if confirm_button.rect.collidepoint(event.pos):
                    # player was right
                    if REAL and TALKING:
                        if DEBUG:
                            print("Player pressed CONFIRM and was CORRECT.")  # DEBUG print
                        # show feedback
                        texts.insert(1, FadingText("Correct!", color=(29, 222, 83), pos=(500, 300)))
                        # stop talking and emote
                        TALKING = False
                        friend.answer_correct()
                        panel.set_text("Well done!")
                        panel.set_color(1)
                        sound = pygame.mixer.Sound('./resources/correct.mp3')
                        sound.play()
                        START_EMOTE = pygame.time.get_ticks()
                        # add score
                        score.add_score(1)
                        for sprite in ui_ending:
                            sprite.update_image()
                    # player was wrong
                    elif not REAL and TALKING:
                        if DEBUG:
                            print("Player pressed CONFIRM and was WRONG.")  # DEBUG print
                        # show feedback
                        texts.insert(1, FadingText("Wrong!", color=(175, 73, 83), pos=(500, 300)))
                        # stop talking and emote
                        TALKING = False
                        friend.answer_incorrect()
                        panel.set_color(2)
                        panel.set_text("That's not right...")
                        sound = pygame.mixer.Sound('./resources/wrong.mp3')
                        sound.play()
                        START_EMOTE = pygame.time.get_ticks()
                        # take damage
                        health.take_damage(1)
                # when we click on Fake
                if deny_button.rect.collidepoint(event.pos):
                    # player was right
                    if not REAL and TALKING:
                        if DEBUG:
                            print("Player pressed DENY and was CORRECT.")  # DEBUG print
                        texts.insert(1, FadingText("Correct!", color=(29, 222, 83), pos=(500, 300)))
                        TALKING = False
                        friend.answer_correct()
                        panel.set_text("Well done!")
                        panel.set_color(1)
                        sound = pygame.mixer.Sound('./resources/correct.mp3')
                        sound.play()
                        START_EMOTE = pygame.time.get_ticks()
                        score.add_score(1)
                        for sprite in ui_ending:
                            sprite.update_image()
                    # player was wrong
                    elif REAL and TALKING:
                        if DEBUG:
                            print("Player pressed DENY and was WRONG.")  # DEBUG print
                        texts.insert(1, FadingText("Wrong!", color=(175, 73, 83), pos=(500, 300)))
                        TALKING = False
                        friend.answer_incorrect()
                        panel.set_text("That's not right...")
                        panel.set_color(2)
                        sound = pygame.mixer.Sound('./resources/wrong.mp3')
                        sound.play()
                        START_EMOTE = pygame.time.get_ticks()
                        health.take_damage(1)
                # when we click on Retry
                if restart_button.rect.collidepoint(event.pos):
                    print("Player wants to try again. Restarting..")
                    print_once.reset()
                    return "restart"

        # clear the screen each frame
        screen.fill((50,50,50))
        bg_group.update(dt)
        bg_group.draw(screen)

        # make friend sprite talk
        # draws the option buttons
        if TALKING and not GAME_OVER:
            pygame.mixer.music.set_volume(0.5)
            panel.set_text("Is this a real word?")
            panel.set_color(0)
            MOOD = 1
            confirm_button.draw(screen)
            deny_button.draw(screen)

        # stop emoting and give another question
        elapsed = pygame.time.get_ticks() - START_EMOTE
        if not TALKING and elapsed > 1200 and not GAME_OVER:
            friend.talk()

        # render stuff
        if GAME_OVER:
            pygame.mixer.music.set_volume(0)
            draw_end_message(screen, "Game Over",pos=(SCREEN_WIDTH // 2, 160))
            print_once("Game ended at score " + str(score.score) + ".")
            restart_button.draw(screen)
            for sprite in ui_ending:
                sprite.update_image()
            ui_ending.draw(screen)
            # tell user if they got a new high score
            if score.score > HIGHSCORE:
                print_once("Player got a high score!")
                # TODO fix the position of this one
                draw_end_message(screen, "New High Score!",
                                 pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60), color=(204, 176, 0))
        else:
            # update sprites

            friend.update()
            for t in texts:
                t.update()
                t.draw(screen)
            friend.draw(screen)
            room_stuff.draw(screen)
            confirm_button.update(dt)
            deny_button.update(dt)
            restart_button.update(dt)
            ui_group.update()
            ui_panel.update(dt)
            ui_health.update(dt)
            ui_group.draw(screen)
            ui_panel.draw(screen)
            ui_health.draw(screen)

        # display update
        pygame.display.flip()

        # FPS
        clock.tick(60)

    # quit
    return "quit"

if __name__ == "__main__":
    while True:
        result = game_loop()
        if result != "restart":
            break
