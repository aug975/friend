import pygame
import math

pygame.init()

# color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

DEFAULT_FONT = pygame.font.SysFont(None, 28)

HIGHSCORE_FILE = "./resources/highscore.txt"

def load_highscore() -> int:
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_highscore(value: int):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(int(value)))
    except Exception as e:
        # print a warning if fails
        print(f"Couldn't save highscore: {e}")

# small text surface helper
def text_surface(font, text, color=(255, 255, 255), bold=False):
    if bold:
        if hasattr(font, "set_bold"):
            font.set_bold(True)
            surf = font.render(text, True, color)
            font.set_bold(False)
        else:
            # fallback
            surf = font.render(text, True, color)
    else:
        surf = font.render(text, True, color)
    return surf

# scary class to make text appear in a bubble
class SpeechBubble:
    def __init__(
        self,
        text: str,
        *,
        text_color=BLACK,
        background=WHITE,
        pos=(0, 0),
        friend_pos=(0, 0),
        font=DEFAULT_FONT,
        bold=False,
        padding=20,
        radius=15,
        tail_length=25,
        tail_width=20
    ):
        self.text = text
        self.text_color = text_color
        self.background = background
        self.pos = pos
        self.friend_pos = friend_pos
        self.font = font
        self.bold = bold
        self.padding = padding
        self.radius = radius
        self.tail_length = tail_length
        self.tail_width = tail_width

        # render text!!
        text_surf = text_surface(self.font, self.text, self.text_color, self.bold)
        text_rect = text_surf.get_rect()

        # bubble rect!!
        self.rect = pygame.Rect(0, 0, text_rect.width + 2 * padding, text_rect.height + 2 * padding)
        self.rect.topleft = pos

        # bubble surface..
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.background, self.image.get_rect(), border_radius=radius)
        self.image.blit(text_surf, (padding, padding))

        # point at menace..
        self._draw_tail()

    def _draw_tail(self):
        # we'll need to do some nerd stuff to make the tail work
        # get the center from the rect, find the angle to Friend
        bubble_center = self.rect.center
        dx, dy = self.friend_pos[0] - bubble_center[0], self.friend_pos[1] - bubble_center[1]
        angle = math.atan2(dy, dx)

        # base of it needs to be near the edge
        edge_x = bubble_center[0] + (self.rect.width // 2) * math.cos(angle)
        edge_y = bubble_center[1] + (self.rect.height // 2) * math.sin(angle)

        # tip needs to be closer to destination
        tip_x = edge_x + self.tail_length * math.cos(angle)
        tip_y = edge_y + self.tail_length * math.sin(angle)

        # corner stuff!!!!!
        perp_angle = angle + math.pi / 2
        base_left = (edge_x + self.tail_width * math.cos(perp_angle) / 2,
                     edge_y + self.tail_width * math.sin(perp_angle) / 2)
        base_right = (edge_x - self.tail_width * math.cos(perp_angle) / 2,
                      edge_y - self.tail_width * math.sin(perp_angle) / 2)

        # adjust it so it's not weird :)
        tip = (tip_x - self.rect.left, tip_y - self.rect.top)
        base_left = (base_left[0] - self.rect.left, base_left[1] - self.rect.top)
        base_right = (base_right[0] - self.rect.left, base_right[1] - self.rect.top)

        # tadaa
        pygame.draw.polygon(self.image, self.background, [base_left, base_right, tip])

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, self.rect)

# class to make text appear, that fades out after
class FadingText:
    def __init__(
        self,
        text: str,
        *,
        pos=(0, 0),
        color=WHITE,
        font=DEFAULT_FONT,
        bold=False,
        lifetime=2000
    ):
        """A temporary text that fades out after `lifetime` ms."""
        self.image = text_surface(font, text, color, bold)
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        self.alpha = 255

    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.lifetime:
            self.alpha = 0
        else:
            self.alpha = max(0, 255 - int(255 * (elapsed / self.lifetime)))
        self.image.set_alpha(self.alpha)

    def draw(self, surface: pygame.Surface):
        if self.alpha > 0:
            surface.blit(self.image, self.rect)

# class for the score counter, also handles the score
# somehow ended up way longer than it should be..
class ScoreCounter(pygame.sprite.Sprite):
    def __init__(
        self,
        *,
        pos=(0, 0),
        font=DEFAULT_FONT,
        color=WHITE,
        text="Score: ",
        high=False,
        groups=None
    ):
        super().__init__(*(groups or []))
        self.font = font
        self.color = color
        self.base_text = text
        self.high = high

        # if this is the highscore one, read from file
        self.score = load_highscore() if self.high else 0

        self.image = text_surface(self.font, self.base_text + str(self.score), self.color)
        self.rect = self.image.get_rect(midtop=pos)

    def add_score(self, points=1):
        if self.high:
            # if you get here somehow you're being dumb
            return

        self.score += int(points)

        # check if we beat the saved highscore and update file
        current_high = load_highscore()
        if self.score > current_high:
            save_highscore(self.score)

        self.update_image()

    def set_score(self, value: int):
        self.score = int(value)
        self.update_image()

    def reset(self):
        if not self.high:
            self.score = 0
            self.update_image()

    def update_image(self):
        if self.high:
            # show what's on disk
            self.score = load_highscore()
            display_text = f"High Score: {self.score}"
        else:
            display_text = f"{self.base_text}{self.score}"

        self.image = text_surface(self.font, display_text, self.color)
        self.rect = self.image.get_rect(midtop=self.rect.midtop)

# function for a gameover message
# "hey man you died, good for you or sorry that happened"
def draw_end_message(
    surface: pygame.Surface,
    message: str,
    *,
    pos=(400, 300),  # fallback default
    color=RED,
    font=DEFAULT_FONT,
    bold=True
):
    text = text_surface(font, message, color, bold)
    rect = text.get_rect(center=pos)
    surface.blit(text, rect)

# Replace your BottomPanel with this implementation
class BottomPanel(pygame.sprite.Sprite):
    def __init__(self, screen_rect, *,
                 height=80,
                 top_color=(180, 220, 255),
                 bottom_color=(42, 66, 74),
                 radius=16,
                 border=6,
                 border_color=(20, 20, 20),
                 font=None,
                 font_color=(0, 0, 0),
                 padding=12,
                 groups=None,
                 clip_bottom=True):
        super().__init__(*(groups or []))
        self.screen_rect = screen_rect
        self.width = screen_rect.width
        self.height = height
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.radius = radius
        self.border = max(0, int(border))
        self.border_color = border_color
        self.font = font or pygame.font.SysFont(None, 28)
        self.font_color = font_color
        self.padding = padding
        self.text = ""
        self.clip_bottom = clip_bottom

        # build image and place it (we will nudge midbottom down by border if clip_bottom)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # place midbottom slightly below screen to hide bottom border (if desired)
        offset = self.border if self.clip_bottom else 0
        self.rect = self.image.get_rect(midbottom=(screen_rect.centerx, screen_rect.bottom + offset))

        self._draw_panel()

    def _make_vertical_gradient(self, size):
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if h <= 0:
            return surf
        for y in range(h):
            t = y / (h - 1) if h > 1 else 0
            r = int(self.top_color[0] * (1 - t) + self.bottom_color[0] * t)
            g = int(self.top_color[1] * (1 - t) + self.bottom_color[1] * t)
            b = int(self.top_color[2] * (1 - t) + self.bottom_color[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        return surf

    def _rounded_mask(self, size, radius):
        """Return an opaque (255 alpha) mask surface with rounded top corners."""
        w, h = size
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        # filled body and top stripe
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, radius, w, h - radius))
        pygame.draw.rect(mask, (255, 255, 255, 255), (radius, 0, w - 2 * radius, radius))
        # top corners
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        pygame.draw.circle(mask, (255, 255, 255, 255), (w - radius, radius), radius)
        return mask

    def _wrap_text(self, text):
        words = text.split()
        lines, current = [], ""
        max_w = self.width - 2 * (self.padding + self.border)
        for word in words:
            test = (current + " " + word).strip()
            tw, _ = self.font.size(test)
            if tw <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_panel(self):
        w, h, r, b = self.width, self.height, self.radius, self.border
        self.image.fill((0, 0, 0, 0))

        # 1) Outer rounded area = border color (filled rounded rect)
        outer = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(outer, self.border_color, outer.get_rect(), border_radius=r)

        # 2) Inner area size and inner radius
        inner_w = max(0, w - 2 * b)
        inner_h = max(0, h - 2 * b)
        inner_radius = max(0, r - b)

        if inner_w > 0 and inner_h > 0:
            # 3) Build gradient for inner area
            grad = self._make_vertical_gradient((inner_w, inner_h))

            # 4) Mask the gradient with a rounded rect mask (so corners are rounded)
            mask = self._rounded_mask((inner_w, inner_h), inner_radius)
            mask_surf = pygame.mask.from_surface(mask).to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0))
            grad.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # 5) Blit inner gradient onto outer (centered with border inset)
            outer.blit(grad, (b, b))

        # 6) Now outer contains border+inner; set as panel image
        self.image.blit(outer, (0, 0))

        # 7) Draw text (inside inner area)
        if self.text:
            lines = self._wrap_text(self.text)
            # vertical center inside inner area
            total_h = sum(self.font.size(line)[1] for line in lines)
            start_y = b + max(0, (inner_h - total_h) // 2)
            y = start_y
            for line in lines:
                surf = self.font.render(line, True, self.font_color)
                rect = surf.get_rect(centerx=w // 2, y=y)
                self.image.blit(surf, rect)
                y += surf.get_height()

    def set_text(self, text: str):
        self.text = text
        self._draw_panel()

# very scary face -> :-)
