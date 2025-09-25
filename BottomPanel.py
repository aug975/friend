import pygame

class BottomPanel(pygame.sprite.Sprite):
    def __init__(self, screen_rect, *,
                 height=80,
                 checker_imgs=None,          # list of 3 image paths
                 checker_alpha=100,
                 scroll_speed=(30, 30),      # px/sec
                 angle=0,                    # rotation degrees (unused for now)
                 bg_color=(200, 200, 200),   # opaque gray background
                 radius=12,
                 border=4,
                 border_color=(20, 20, 20),
                 font=None,
                 font_color=(0, 0, 0),
                 groups=None):
        super().__init__(*(groups or []))
        self.width = screen_rect.width
        self.height = height
        self.radius = radius
        self.border = border
        self.border_color = border_color
        self.font = font or pygame.font.SysFont(None, 28)
        self.font_color = font_color
        self.text = ""

        # --- Checkerboard setup ---
        # Store paths for swapping later
        self.checker_imgs = checker_imgs or [
            "./resources/checker.png",
            "./resources/checker_c.png",
            "./resources/checker_w.png",
        ]
        self.checker_alpha = checker_alpha
        self.scroll_speed = scroll_speed
        self.offset = [0.0, 0.0]

        # start with the first checker texture
        self.checker_index = 0
        self.checker_texture = pygame.image.load(self.checker_imgs[self.checker_index]).convert_alpha()

        self.bg_color = bg_color

        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=screen_rect.midbottom)

        self._draw_panel()

    def _blit_checkerboard(self, target):
        tex = self.checker_texture
        tw, th = tex.get_size()
        ox, oy = int(self.offset[0]) % tw, int(self.offset[1]) % th

        temp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for x in range(-ox, self.width, tw):
            for y in range(-oy, self.height, th):
                temp.blit(tex, (x, y))
        temp.set_alpha(self.checker_alpha)
        target.blit(temp, (0, 0))

    def _draw_panel(self):
        self.image.fill((0, 0, 0, 0))
        panel_rect = self.image.get_rect()

        # --- master mask for rounded shape ---
        mask = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), panel_rect, border_radius=self.radius)

        # --- background solid ---
        bg_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        bg_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # --- checkerboard overlay ---
        checker_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._blit_checkerboard(checker_surf)
        checker_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # --- shadow gradient overlay ---
        grad_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        fade_height = int(self.height * 0.2)
        max_alpha = 90
        for y in range(fade_height):
            alpha = max_alpha - int(max_alpha * (y / fade_height))
            pygame.draw.line(grad_surf, (0, 0, 0, alpha), (0, y), (self.width, y))
        grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # --- composite all into self.image ---
        self.image.blit(bg_surf, (0, 0))
        self.image.blit(checker_surf, (0, 0))
        self.image.blit(grad_surf, (0, 0))

        # --- border (drawn last) ---
        if self.border > 0:
            pygame.draw.rect(self.image, self.border_color, panel_rect,
                             self.border, border_radius=self.radius)

        # --- text (with shadow) ---
        if self.text:
            text_surf = self.font.render(self.text, True, self.font_color)
            text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))

            shadow_offset = (2, 2)
            shadow_surf = self.font.render(self.text, True, (140, 140, 140))
            shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + shadow_offset[0],
                                                       text_rect.centery + shadow_offset[1]))
            self.image.blit(shadow_surf, shadow_rect)
            self.image.blit(text_surf, text_rect)

    def set_text(self, text: str):
        self.text = text
        self._draw_panel()

    def set_color(self, color: int):
        """Swap checker texture based on index 0/1/2"""
        if 0 <= color < len(self.checker_imgs):
            self.checker_index = color
            self.checker_texture = pygame.image.load(self.checker_imgs[color]).convert_alpha()
            self._draw_panel()

    def update(self, dt):
        self.offset[0] += self.scroll_speed[0] * dt
        self.offset[1] += self.scroll_speed[1] * dt
        self._draw_panel()
