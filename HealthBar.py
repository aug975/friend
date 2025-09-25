import pygame, math, random

class HealthBar(pygame.sprite.Sprite):
    def __init__(self, x, y, group,
                 width=200, height=25, max_health=100,
                 color=(0, 255, 0),
                 bg_pattern=None, fg_pattern=None,
                 border_color=(255, 255, 255), border_thickness=3,
                 shadow_offset=(4, 4)):
        super().__init__(group)

        # --- config ---
        self.max_health = max_health
        self.current_health = max_health
        self.width = width
        self.height = height
        self.color = color
        self.x = x
        self.y = y

        # --- parallax ---
        self.bg_pattern = pygame.image.load(bg_pattern).convert_alpha() if bg_pattern else None
        self.fg_pattern = pygame.image.load(fg_pattern).convert_alpha() if fg_pattern else None
        self.bg_offset = [0.0, 0.0]
        self.fg_offset = [0.0, 0.0]
        self.bg_speed = (10, 10)   # slower background
        self.fg_speed = (30, 30)   # faster foreground

        # --- border & shadow ---
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.shadow_offset = shadow_offset

        # --- shake effect ---
        self.shake_duration = 0.3   # seconds
        self.shake_remaining = 0.0
        self.shake_deg = 5          # max angle
        self.shake_jitter = 2       # px jitter

        # sprite setup
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self._rebuild_base()

    # ---------------------------------------
    def _blit_parallax(self, target, tex, offset):
        if not tex:
            return
        tw, th = tex.get_size()
        if tw == 0 or th == 0:
            return
        ox, oy = int(offset[0]) % tw, int(offset[1]) % th
        for xx in range(-ox, target.get_width(), tw):
            for yy in range(-oy, target.get_height(), th):
                target.blit(tex, (xx, yy))

    # ---------------------------------------
    def take_damage(self, amount):
        self.current_health = max(0, self.current_health - amount)
        self.shake_remaining = self.shake_duration
        self._rebuild_base()

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)
        self._rebuild_base()

    # ---------------------------------------
    def _rebuild_base(self):
        """Rebuilds the static bar surface without shake."""
        w, h = max(1, self.width), max(1, self.height)
        bar = pygame.Surface((w, h), pygame.SRCALPHA)

        # --- background (lost HP area) ---
        dark_gray = (40, 40, 40)
        pygame.draw.rect(bar, dark_gray, (0, 0, w, h))
        if self.bg_pattern:
            self._blit_parallax(bar, self.bg_pattern, self.bg_offset)

        # --- foreground (current HP) ---
        ratio = max(0.0, min(1.0, float(self.current_health) / float(self.max_health)))
        fg_w = max(0, int(round(w * ratio)))
        if fg_w > 0:
            fg_surf = pygame.Surface((fg_w, h), pygame.SRCALPHA)
            fg_surf.fill(self.color)
            if self.fg_pattern:
                self._blit_parallax(fg_surf, self.fg_pattern, self.fg_offset)
            bar.blit(fg_surf, (0, 0))

        # --- border ---
        pygame.draw.rect(bar, self.border_color, bar.get_rect(), self.border_thickness)

        self.bar_surface = bar

    # ---------------------------------------
    def update(self, dt=16):
        """Update parallax + shake. dt in ms."""

        # --- scroll parallax ---
        self.bg_offset[0] += self.bg_speed[0] * dt
        self.bg_offset[1] += self.bg_speed[1] * dt
        self.fg_offset[0] += self.fg_speed[0] * dt
        self.fg_offset[1] += self.fg_speed[1] * dt

        # rebuild base with new offsets
        self._rebuild_base()

        # --- shadow base ---
        shadow = pygame.Surface(self.bar_surface.get_size(), pygame.SRCALPHA)
        shadow.blit(self.bar_surface, (0, 0))
        shadow.set_alpha(120)

        # --- shake effect ---
        if self.shake_remaining > 0.0:
            self.shake_remaining -= dt
            t = max(0.0, self.shake_remaining / self.shake_duration)  # 1 → 0 as it fades

            angle = math.sin(pygame.time.get_ticks() * 0.05) * (self.shake_deg * t)
            jx = random.randint(-self.shake_jitter, self.shake_jitter) * t
            jy = random.randint(-self.shake_jitter, self.shake_jitter) * t

            rotated = pygame.transform.rotate(self.bar_surface, angle)
            self.image = pygame.Surface((rotated.get_width() + self.shadow_offset[0],
                                         rotated.get_height() + self.shadow_offset[1]),
                                        pygame.SRCALPHA)
            # shadow first
            shadow_rot = pygame.transform.rotate(shadow, angle)
            self.image.blit(shadow_rot, self.shadow_offset)
            # then shaken bar
            self.image.blit(rotated, (0, 0))
            self.rect = self.image.get_rect(center=(self.x + self.width // 2 + jx,
                                                    self.y + self.height // 2 + jy))
        else:
            # normal mode
            self.image = pygame.Surface((self.bar_surface.get_width() + self.shadow_offset[0],
                                         self.bar_surface.get_height() + self.shadow_offset[1]),
                                        pygame.SRCALPHA)
            self.image.blit(shadow, self.shadow_offset)
            self.image.blit(self.bar_surface, (0, 0))
            self.rect = self.image.get_rect(topleft=(self.x, self.y))
