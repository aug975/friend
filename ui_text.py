import pygame
import math

pygame.init()

# color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

DEFAULT_FONT = pygame.font.SysFont(None, 28)
score_font = pygame.font.Font('./resources/Titania-Regular.ttf', 32)
over_font = pygame.font.Font('./resources/Leander.ttf', 68)
message_font = pygame.font.Font('./resources/OldNewspaperTypes.ttf', 64)

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

def render_text_with_outline(font, text, text_color, outline_color, outline_thickness=2):
    # render the main text
    text_surf = font.render(text, True, text_color)
    w, h = text_surf.get_size()

    # surface with space for outline
    surf = pygame.Surface((w + 2*outline_thickness, h + 2*outline_thickness), pygame.SRCALPHA)

    # render outline by shifting text around
    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx**2 + dy**2 <= outline_thickness**2:  # circular outline
                outline_surf = font.render(text, True, outline_color)
                surf.blit(outline_surf, (dx + outline_thickness, dy + outline_thickness))

    # render main text centered
    surf.blit(text_surf, (outline_thickness, outline_thickness))

    return surf

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
    def __init__(self, text, *,
                 text_color=(0,0,0), background=(255,255,255),
                 pos=(0,0), friend_pos=(0,0),
                 font=None, padding=20, radius=15,
                 tail_length=25, tail_width=20,
                 border=4, border_color=(0,0,0)):
        self.text = text
        self.text_color = text_color
        self.background = background
        self.friend_pos = friend_pos
        self.font = font or pygame.font.SysFont(None, 32)
        self.padding = padding
        self.radius = radius
        self.tail_length = tail_length
        self.tail_width = tail_width
        self.border = border
        self.border_color = border_color

        # render text
        text_surf = self.font.render(text, True, text_color)
        text_rect = text_surf.get_rect()

        # bubble rect (not including tail)
        bubble_w = text_rect.width + 2*padding
        bubble_h = text_rect.height + 2*padding
        self.bubble_rect = pygame.Rect(0, 0, bubble_w, bubble_h)

        # margin for tail
        margin = tail_length + border + 2
        self.image = pygame.Surface((bubble_w + margin*2, bubble_h + margin*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(pos[0]-margin, pos[1]-margin))

        self.bubble_rect.topleft = (margin, margin)

        # draw bubble fill
        pygame.draw.rect(self.image, background, self.bubble_rect, border_radius=radius)

        # draw text
        self.image.blit(text_surf, (self.bubble_rect.left + padding, self.bubble_rect.top + padding))

        # draw tail + outline
        self._draw_bubble_with_tail()

    def _draw_bubble_with_tail(self):
        fx, fy = self.friend_pos
        local_fx, local_fy = fx - self.rect.left, fy - self.rect.top
        cx, cy = self.bubble_rect.center
        dx, dy = local_fx - cx, local_fy - cy
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        ux, uy = dx / dist, dy / dist
        half_w, half_h = self.bubble_rect.width / 2, self.bubble_rect.height / 2
        eps = 1e-6
        tx = (half_w / abs(ux)) if abs(ux) > eps else float("inf")
        ty = (half_h / abs(uy)) if abs(uy) > eps else float("inf")
        t = min(tx, ty)

        # --- move base slightly *inside* bubble to avoid seam ---
        overlap_px = self.border
        base_cx, base_cy = cx + ux * (t - overlap_px), cy + uy * (t - overlap_px)

        px, py = -uy, ux
        half_base = self.tail_width / 2
        base_left = (base_cx + px * half_base, base_cy + py * half_base)
        base_right = (base_cx - px * half_base + 10, base_cy - py * half_base - 10)

        tip_len = min(self.tail_length, max(4, dist - t))
        tip_x, tip_y = base_cx + ux * tip_len, base_cy + uy * tip_len + 20
        tail_poly = [base_left, base_right, (tip_x, tip_y)]

        # --- make one filled shape (bubble + tail) ---
        shape = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(shape, self.background, self.bubble_rect, border_radius=self.radius)
        pygame.draw.polygon(shape, self.background, tail_poly)

        # --- copy to final image ---
        self.image.blit(shape, (0, 0))

        # --- outline the whole shape ---
        mask = pygame.mask.from_surface(shape)
        outline_points = mask.outline()
        if outline_points:
            pygame.draw.lines(self.image, self.border_color, True, outline_points, self.border)

        # --- text with shadow ---
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.bubble_rect.center)

        shadow_offset = (2, 2)
        shadow_surf = self.font.render(self.text, True, (200, 200, 200))
        shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + shadow_offset[0],
                                                   text_rect.centery + shadow_offset[1]))
        self.image.blit(shadow_surf, shadow_rect)
        self.image.blit(text_surf, text_rect)

    def draw(self, surface):
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
        text_surf = render_text_with_outline(
            message_font,
            text,
            text_color=color,          # inside color
            outline_color=(0, 0, 0), # outline color
            outline_thickness=2
        )
        self.image = text_surf
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
        font=score_font,
        color=WHITE,
        text="",
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

        text_surf = render_text_with_outline(
            self.font,
            self.base_text + str(self.score),
            text_color=self.color,          # inside color
            outline_color=(0, 0, 0), # outline color
            outline_thickness=2
        )

        self.image = text_surf
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

        text_surf = render_text_with_outline(
            self.font,
            display_text,
            text_color=self.color,          # inside color
            outline_color=(0, 0, 0), # outline color
            outline_thickness=2
        )

        self.image = text_surf
        self.rect = self.image.get_rect(midtop=self.rect.midtop)

# function for a gameover message
# "hey man you died, good for you or sorry that happened"
def draw_end_message(
    surface: pygame.Surface,
    message: str,
    *,
    pos=(400, 300),  # fallback default
    color=RED,
    font=over_font,
    bold=True
):

    text_surf = render_text_with_outline(
            font,
            message,
            text_color=color,          # inside color
            outline_color=(0, 0, 0), # outline color
            outline_thickness=2
        )
    text = text_surf
    rect = text.get_rect(center=pos)
    surface.blit(text, rect)

# very scary face -> :-)
