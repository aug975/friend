import pygame
import random
import sys

# potential api i could use for this
# https://www.wordsapi.com/

# start pygame
pygame.init()

# window
# on my last version I HAD THE WIDTH AND HEIGHT BACKWARDS ;w;
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# lazy solution
def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper
@run_once
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

# resize the images with the SCALE global variable
friendNeutral = pygame.transform.scale(friendNeutral,
                                       (friendNeutral.get_size()[0] * SCALE, friendNeutral.get_size()[1] * SCALE))
friendTalk = pygame.transform.scale(friendTalk, (friendTalk.get_size()[0] * SCALE, friendTalk.get_size()[1] * SCALE))
friendHappy = pygame.transform.scale(friendHappy,
                                     (friendHappy.get_size()[0] * SCALE, friendHappy.get_size()[1] * SCALE))
friendSad = pygame.transform.scale(friendSad, (friendSad.get_size()[0] * SCALE, friendSad.get_size()[1] * SCALE))

# function to create text surfaces (to simplify the code for the text classes)
def text_surface_with_font(font: pygame.font.Font, text: str, color, bold=False):
    font.set_bold(bold)
    return font.render(text, True, color).convert_alpha()

# TODO a lot of these text classes/functions are kind of messy, I could make some generic text stuff to save space
# (but would it save space..?)

# function for a gameover message
def draw_end_message(surface, message, color=(255, 0, 0), font_size=72, pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)):
    font = pygame.font.SysFont(None, font_size, bold=True)
    text = text_surface_with_font(font, message, color, bold=True)
    rect = text.get_rect(center=pos)
    surface.blit(text, rect)

# class for the health bar, also handles the health numbers
# just a placeholder for now
# is it better to have the health in here, or as a global number..?
class HealthBar(pygame.sprite.Sprite):
    def __init__(self, x, y, group, width=200, height=25, max_health=100, color=(0, 255, 0)):
        super().__init__()
        self.max_health = max_health
        self.current_health = max_health
        self.width = width
        self.height = height
        self.color = color
        self.x = x
        self.y = y

        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.update_image()
        super().__init__(group)

    # for when we want to reduce the player's health
    def take_damage(self, amount):
        self.current_health = max(0, self.current_health - amount)
        self.update_image()

    # for if the player heals some health (unused for now)
    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)
        self.update_image()

    def update_image(self):
        self.image.fill((0, 0, 0, 0))  # clear
        ratio = self.current_health / self.max_health
        pygame.draw.rect(self.image, (255, 0, 0), (0, 0, self.width, self.height))  # red background
        pygame.draw.rect(self.image, self.color, (0, 0, self.width * ratio, self.height))  # green foreground
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.width, self.height), 2)  # border

    # for potential effects if I make any
    def update(self):
        pass

# class to make text appear in a bubble
class SpeechBubble:
    def __init__(self, text, text_color, background, pos, friend_pos, bold=False, padding=20, radius=15,
                 tail_length=25, tail_width=30):
        # make text
        text_surf = text_surface_with_font(DEFAULT_FONT, text, text_color, bold)
        text_rect = text_surf.get_rect()

        # bubble size
        w, h = text_rect.width + padding, text_rect.height + padding
        self.image = pygame.Surface((w, h + tail_length), pygame.SRCALPHA)

        # draw rounded rectangle for bubble body
        pygame.draw.rect(self.image, background, (0, 0, w, h), border_radius=radius)

        # center text on bubble
        tr = text_surf.get_rect(center=(w // 2, h // 2))
        self.image.blit(text_surf, tr)

        # bubble rect on screen
        self.rect = self.image.get_rect(center=pos)

        # I could NOT figure out how to make the tail triangular perfectly
        # draw tail
        fx, fy = friend_pos

        # bubble bottom center (in local coords)
        cx = w // 2
        base_y = h

        # tail base points (a small horizontal line at bubble’s bottom)
        half_base = tail_width // 3
        left_base = (cx - half_base - 5, base_y)
        right_base = (cx + half_base, base_y)

        # tail tip: friend position relative to bubble surface
        tip_x = fx - self.rect.left
        tip_y = fy - self.rect.top

        # make sure tip is BELOW bubble bottom
        if tip_y < base_y + 5:
            tip_y = base_y + 5

        # draw triangle tail
        pygame.draw.polygon(self.image, background, [left_base, right_base, (tip_x + 30, tip_y - 40)])

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# class for the score counter, also handles the score
# same question here as the health, should it be separate..?
class ScoreCounter(pygame.sprite.Sprite):
    # need to pull the global here
    global HIGHSCORE

    # the parameter HIGH is for whether it's the high score counter instead
    def __init__(self, x, y, group, font_size=36, color=(255, 255, 255), text="Score: ", high=False):
        # I don't really know why I put super init here
        # I'm scared to change it though I'll leave it here
        super().__init__()
        self.font = pygame.font.SysFont(None, font_size)
        self.color = color
        self.high = high
        # different behavior if it's the regular score counter,
        # or the high score counter
        if self.high:
            self.score = HIGHSCORE
        else:
            self.score = 0

        # initial render
        self.image = text_surface_with_font(self.font, text + str(self.score), self.color)
        self.rect = self.image.get_rect(midtop=(x, y))
        super().__init__(group)

    # add score
    def add_score(self, points=1):
        global HIGHSCORE
        if not self.high:
            self.score += points
            # if the score beats the high score, update it
            if self.score > HIGHSCORE:
                file2 = open("./resources/highscore.txt", "w")
                file2.write(str(self.score))
                file2.close()
                HIGHSCORE = self.score
            self.update_image()

    # reset the score (unused)
    def reset(self):
        if not self.high:
            self.score = 0
            self.update_image()

    def update_image(self):
        global HIGHSCORE
        if self.high:
            self.score = HIGHSCORE
            self.image = text_surface_with_font(self.font, f"High Score: {HIGHSCORE}", self.color)
        else:
            self.image = text_surface_with_font(self.font, f"Score: {self.score}", self.color)
        self.rect = self.image.get_rect(midtop=self.rect.midtop)

    # potentially for effects
    def update(self):
        pass

# class to make text appear, that fades out after
class FadingText:
    # lifetime is in milliseconds
    def __init__(self, text, color, pos, bold=False, lifetime=2000):
        self.image = text_surface_with_font(DEFAULT_FONT, text, color, bold)
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        self.alpha = 255
        self.alive = True

    def update(self):
        # how long since it started
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.lifetime:
            self.alive = False
        else:
            # fade alpha based on progress
            progress = elapsed / self.lifetime
            self.alpha = 255 * (1 - progress)
        # it was complaining about having a float here
        # so I rounded it...
        self.image.set_alpha(round(self.alpha))

    def draw(self, surface):
        # don't draw it if it finished fading out
        if self.alive:
            surface.blit(self.image, self.rect)

# button sprite class
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, active, text="", font=pygame.font.SysFont(None, 28)):
        pygame.sprite.Sprite.__init__(self)
        self.active = active
        self.font = font
        self.text = text

        text_surf = text_surface_with_font(self.font, self.text, (0, 0, 0))
        text_size = text_surf.get_size()
        w, h = text_size[0] * 2, text_size[1] * 2

        self.image = pygame.Surface((w, h))
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        # x, y = self.rect.center
        # color = (182, 218, 206)

        text_surf = text_surface_with_font(self.font, self.text, (0, 0, 0))
        text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))

        # change colors
        if self.active:
            # get a little darker if the mouse is on it
            if self.rect.collidepoint(mouse_pos):
                color = (140, 166, 157)
                self.image.fill(color)
                self.image.blit(text_surf, text_rect)
                screen.blit(self.image, self.rect)
            else:
                color = (182, 218, 206)
                self.image.fill(color)
                self.image.blit(text_surf, text_rect)
                screen.blit(self.image, self.rect)
        # permanently darker while inactive
        else:
            color = (140, 166, 157)
            self.image.fill(color)
            self.image.blit(text_surf, text_rect)
            screen.blit(self.image, self.rect)

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
        self.bubble = SpeechBubble(talk_choice, (0, 0, 0), (255, 255, 255),
                                   (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2), self.rect.center)

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
        if self.bubble:  # draw bubble if it exists
            self.bubble.draw(surface)

# game loop
def game_loop():
    global MOOD, TALKING, START_EMOTE, GAME_OVER, HIGHSCORE
    print("Hello! Loading..")
    # sprite groups
    friend_group = pygame.sprite.GroupSingle()
    ui_group = pygame.sprite.Group()
    ui_ending = pygame.sprite.Group()
    # log the highscore at the beginning of the round
    highscore_old = HIGHSCORE
    # game isn't over if it just started!!
    GAME_OVER = False
    # main loop boolean
    print("Starting game..")
    running = True
    # friend add friend
    friend = Friend(friend_group)
    # all the fading texts are here
    texts = []
    # define the buttons
    confirm_button = Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 200, True, "Yes")
    deny_button = Button(SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT // 2 + 200, True, "No")
    restart_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200, True, "Retry")
    # define counters
    score = ScoreCounter(SCREEN_WIDTH // 2, 10, font_size=40, color=(255, 255, 0), group=ui_group)
    ScoreCounter(SCREEN_WIDTH // 2, 40, font_size=30, color=(255, 255, 0), text="High Score: ", high=True,
                 group=ui_group)
    ScoreCounter(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100, font_size=30, color=(255, 255, 0),
                 text="High Score: ", high=True, group=ui_ending)
    health = HealthBar(20, 20, max_health=3, group=ui_group)

    # friend starts talking right away
    friend.talk()

    while running:
        # game over if the health runs out
        if health.current_health <= 0:
            GAME_OVER = True
        for event in pygame.event.get():
            # handle window closing
            if event.type == pygame.QUIT:
                print("Player wants to exit. Closing...")
                sys.exit()
            # handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # when we click on Real
                if confirm_button.rect.collidepoint(event.pos):
                    # player was right
                    if REAL and TALKING:
                        if DEBUG:
                            print("Player pressed CONFIRM and was CORRECT.")  # DEBUG print
                        # show feedback
                        texts.insert(1, FadingText("Correct!", (29, 222, 83), (500, 300), True))
                        # stop talking and emote
                        TALKING = False
                        friend.answer_correct()
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
                        texts.insert(1, FadingText("Wrong!", (175, 73, 83), (500, 300), True))
                        # stop talking and emote
                        TALKING = False
                        friend.answer_incorrect()
                        START_EMOTE = pygame.time.get_ticks()
                        # take damage
                        health.take_damage(1)
                # when we click on Fake
                if deny_button.rect.collidepoint(event.pos):
                    # player was right
                    if not REAL and TALKING:
                        if DEBUG:
                            print("Player pressed DENY and was CORRECT.")  # DEBUG print
                        texts.insert(1, FadingText("Correct!", (29, 222, 83), (500, 300), True))
                        TALKING = False
                        friend.answer_correct()
                        START_EMOTE = pygame.time.get_ticks()
                        score.add_score(1)
                        for sprite in ui_ending:
                            sprite.update_image()
                    # player was wrong
                    elif REAL and TALKING:
                        if DEBUG:
                            print("Player pressed DENY and was WRONG.")  # DEBUG print
                        texts.insert(1, FadingText("Wrong!", (175, 73, 83), (500, 300), True))
                        TALKING = False
                        friend.answer_incorrect()
                        START_EMOTE = pygame.time.get_ticks()
                        health.take_damage(1)
                # when we click on Retry
                if restart_button.rect.collidepoint(event.pos):
                    print("Player wants to try again. Restarting..")
                    # TODO probably shouldn't use recursion
                    game_loop()

        # clear the screen each frame
        screen.fill((0, 0, 0))

        # make friend sprite talk
        # draws the option buttons
        if TALKING and not GAME_OVER:
            MOOD = 1
            confirm_button.draw(screen)
            deny_button.draw(screen)

        # stop emoting and give another question
        elapsed = pygame.time.get_ticks() - START_EMOTE
        if not TALKING and elapsed > 2000 and not GAME_OVER:
            friend.talk()

        # render stuff
        if GAME_OVER:
            draw_end_message(screen, "Game Over")
            print_once("Game ended at score " + str(score.score) + ".")
            restart_button.draw(screen)
            for sprite in ui_ending:
                sprite.update_image()
            ui_ending.draw(screen)
            # tell user if they got a new high score
            if HIGHSCORE > highscore_old:
                print_once("Player got a high score!")
                # TODO fix the position of this one
                draw_end_message(screen, "New High Score", (197, 224, 37),
                                 pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 300))
        else:
            # update sprites
            friend.update()
            for t in texts:
                t.update()
                t.draw(screen)
                # begone
                if not t.alive:
                    texts.remove(t)
            ui_group.update()
            ui_group.draw(screen)

            # draw friend stuff
            friend.draw(screen)

        # display update
        pygame.display.flip()

        # FPS
        clock.tick(60)

if __name__ == "__main__":
    game_loop()
