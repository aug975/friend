import pygame
import random
import sys
from ui_text import text_surface as text_surface_with_font, SpeechBubble, FadingText, ScoreCounter, draw_end_message, BottomPanel, WHITE, BLACK

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

# resize the images with the SCALE global variable
friendNeutral = pygame.transform.scale(friendNeutral,
                                       (friendNeutral.get_size()[0] * SCALE, friendNeutral.get_size()[1] * SCALE))
friendTalk = pygame.transform.scale(friendTalk, (friendTalk.get_size()[0] * SCALE, friendTalk.get_size()[1] * SCALE))
friendHappy = pygame.transform.scale(friendHappy,
                                     (friendHappy.get_size()[0] * SCALE, friendHappy.get_size()[1] * SCALE))
friendSad = pygame.transform.scale(friendSad, (friendSad.get_size()[0] * SCALE, friendSad.get_size()[1] * SCALE))

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
        pygame.draw.rect(self.image, WHITE, (0, 0, self.width, self.height), 2)  # border

    # for potential effects if I make any
    def update(self):
        pass

# button sprite class
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, active, text="", font=pygame.font.SysFont(None, 28)):
        pygame.sprite.Sprite.__init__(self)
        self.active = active
        self.font = font
        self.text = text

        text_surf = text_surface_with_font(self.font, self.text, BLACK)
        text_size = text_surf.get_size()
        w, h = text_size[0] * 2, text_size[1] * 2

        self.image = pygame.Surface((w, h))
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        # x, y = self.rect.center
        # color = (182, 218, 206)

        text_surf = text_surface_with_font(self.font, self.text, BLACK)
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
        self.bubble = SpeechBubble(talk_choice, pos=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2), friend_pos=self.rect.center)

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
    room_stuff = pygame.sprite.Group()
    ui_group = pygame.sprite.Group()
    ui_ending = pygame.sprite.Group()
    # game isn't over if it just started!!
    GAME_OVER = False
    # main loop boolean
    print("Starting game..")
    running = True
    # friend add friend
    friend = Friend(friend_group)
    StaticSprite('./resources/table.png',(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 295),room_stuff)

    screen_rect = screen.get_rect()
    # the panel!!
    panel = BottomPanel(
        screen_rect,
        height=80,
        border=4,
        top_color=(93, 137, 159),
        bottom_color=(42, 66, 74),
        radius=10,
        groups=(ui_group,)
    )

    # all the fading texts are here
    texts = []
    # define the buttons
    confirm_button = Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 200, True, "Yes")
    deny_button = Button(SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT // 2 + 200, True, "No")
    restart_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200, True, "Retry")
    # define counters
    score = ScoreCounter(pos=(SCREEN_WIDTH // 2, 10), color=(255, 255, 0), groups=(ui_group,),font=BIG_FONT)
    ScoreCounter(pos=(SCREEN_WIDTH // 2, 50), color=(255, 255, 0), text="High Score: ", high=True,
                 groups=(ui_group,), font=SMALL_FONT)
    ScoreCounter(pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), color=(255, 255, 0),
                 text="High Score: ", high=True, groups=(ui_ending,))
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
                        panel.set_text("That's not right...")
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
                        START_EMOTE = pygame.time.get_ticks()
                        health.take_damage(1)
                # when we click on Retry
                if restart_button.rect.collidepoint(event.pos):
                    print("Player wants to try again. Restarting..")
                    print_once.reset()
                    # TODO probably shouldn't use recursion
                    game_loop()

        # clear the screen each frame
        screen.fill(BLACK)

        # make friend sprite talk
        # draws the option buttons
        if TALKING and not GAME_OVER:
            panel.set_text("Is this a real word?")
            MOOD = 1
            confirm_button.draw(screen)
            deny_button.draw(screen)

        # stop emoting and give another question
        elapsed = pygame.time.get_ticks() - START_EMOTE
        if not TALKING and elapsed > 2000 and not GAME_OVER:
            friend.talk()

        # render stuff
        if GAME_OVER:
            draw_end_message(screen, "Game Over",font=BIGGER_FONT,pos=(SCREEN_WIDTH // 2, 160))
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
            ui_group.update()
            ui_group.draw(screen)

        # display update
        pygame.display.flip()

        # FPS
        clock.tick(60)

if __name__ == "__main__":
    game_loop()
