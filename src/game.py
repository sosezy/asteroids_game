"""Главный класс приложения: игровой цикл, события, коллизии и рендеринг."""

import pygame

from src import config
from src.entities import Asteroid, Explosion, Missile, Ship
from src.sprites import load_assets


class AsteroidsGame:
    """Управляет окном, состоянием игры, вводом игрока и отрисовкой."""

    def __init__(self) -> None:
        """Инициализировать Pygame, окно, ресурсы и начальное состояние."""
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.hud_font = pygame.font.SysFont(
            config.UI_FONT_NAME, 24, bold=True
        )

        self.assets = load_assets()
        self.splash_rect = self.assets.splash.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        )

        # Состояние игры
        self.running = True
        self.in_game = False
        self.lives = config.INITIAL_LIVES
        self.score = config.INITIAL_SCORE
        self.debris_offset_x = 0.0
        self.spawn_timer = 0.0

        # Игровые сущности
        self.ship = Ship(self.assets.ship_tiles, self.assets.missile)
        self.asteroids: list[Asteroid] = []
        self.missiles: list[Missile] = []
        self.explosions: list[Explosion] = []

    def start_game(self) -> None:
        """Запустить новую игровую сессию после клика по заставке."""
        self.lives = config.INITIAL_LIVES
        self.score = config.INITIAL_SCORE
        self.spawn_timer = 0.0
        self.asteroids.clear()
        self.missiles.clear()
        self.explosions.clear()
        self.ship.reset()
        self.in_game = True

    def end_game(self) -> None:
        """Завершить игру и вернуть заставку, сохранив счёт и жизни."""
        self.in_game = False
        self.asteroids.clear()
        self.missiles.clear()
        self.explosions.clear()
        self.ship.reset()

    def _handle_events(self) -> None:
        """Обработать события окна, мыши и нажатий клавиш."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Запуск игры только по клику внутри прямоугольника заставки
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and not self.in_game
            ):
                if self.splash_rect.collidepoint(event.pos):
                    self.start_game()

            # Одиночный выстрел ракетой по нажатию пробела
            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_SPACE
                and self.in_game
            ):
                self.missiles.append(self.ship.shoot())

        if self.in_game:
            keys = pygame.key.get_pressed()
            rotation_dir = int(keys[pygame.K_LEFT]) - int(keys[pygame.K_RIGHT])
            self.ship.set_rotation(rotation_dir)
            self.ship.set_thrust(bool(keys[pygame.K_UP]))

    def _update_spawner(self, dt: float) -> None:
        """Периодически генерировать новые астероиды на игровом поле."""
        self.spawn_timer += dt
        if self.spawn_timer < config.ASTEROID_SPAWN_INTERVAL:
            return
        self.spawn_timer = 0.0
        if len(self.asteroids) < config.ASTEROID_MAX_COUNT:
            asteroid = Asteroid.spawn_random(
                image=self.assets.asteroid,
                avoid_pos=(self.ship.pos[0], self.ship.pos[1]),
            )
            self.asteroids.append(asteroid)

    def _handle_collisions(self) -> None:
        """Обработать столкновения ракет и корабля с астероидами."""
        # 1. Столкновения ракет с астероидами
        remaining_missiles: list[Missile] = []
        for missile in self.missiles:
            hit_asteroid = None
            for asteroid in self.asteroids:
                if missile.collides_with(asteroid):
                    hit_asteroid = asteroid
                    break

            if hit_asteroid is not None:
                self.asteroids.remove(hit_asteroid)
                self.explosions.append(
                    Explosion(
                        (hit_asteroid.pos[0], hit_asteroid.pos[1]),
                        self.assets.explosion_frames,
                    )
                )
                self.score += 1
            else:
                remaining_missiles.append(missile)
        self.missiles = remaining_missiles

        # 2. Столкновение корабля с астероидом (астероиды между собой не бьются)
        for asteroid in list(self.asteroids):
            if self.ship.collides_with(asteroid):
                self.asteroids.remove(asteroid)
                self.explosions.append(
                    Explosion(
                        (asteroid.pos[0], asteroid.pos[1]),
                        self.assets.explosion_frames,
                    )
                )
                self.lives -= 1
                if self.lives <= 0:
                    self.lives = 0
                    self.end_game()
                    return
                self.ship.reset()
                break

    def _update(self, dt: float) -> None:
        """Обновить фон и все активные игровые объекты за шаг dt."""
        # Бесшовное движение полупрозрачного слоя астероидов влево
        self.debris_offset_x = (
            self.debris_offset_x - config.DEBRIS_SCROLL_SPEED * dt
        ) % config.SCREEN_WIDTH

        if not self.in_game:
            return

        self._update_spawner(dt)
        self.ship.update(dt)

        for asteroid in self.asteroids:
            asteroid.update(dt)

        self.missiles = [
            missile for missile in self.missiles if not missile.update(dt)
        ]
        self.explosions = [
            exp for exp in self.explosions if not exp.update(dt)
        ]

        self._handle_collisions()

    def _draw_hud_panel(self, rect: pygame.Rect) -> None:
        """Отрисовать полупрозрачную контрастную подложку для элемента HUD."""
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel, config.COLOR_HUD_BG, panel.get_rect(), border_radius=12
        )
        pygame.draw.rect(
            panel,
            (*config.COLOR_HUD_BORDER, 190),
            panel.get_rect(),
            width=2,
            border_radius=12,
        )
        self.screen.blit(panel, rect.topleft)

    def _draw_life_icon(
        self, center: tuple[int, int], active: bool
    ) -> None:
        """Отрисовать мини-иконку сердца для наглядного показа жизней."""
        cx, cy = center
        color = config.COLOR_LIFE_ACTIVE if active else config.COLOR_LIFE_LOST
        pygame.draw.circle(self.screen, color, (cx - 4, cy - 2), 5)
        pygame.draw.circle(self.screen, color, (cx + 4, cy - 2), 5)
        pygame.draw.polygon(
            self.screen,
            color,
            [(cx - 9, cy), (cx + 9, cy), (cx, cy + 9)],
        )

    def _draw_hud(self) -> None:
        """Отрисовать чёткие панели с количеством жизней и счётом."""
        # Левая панель: Жизни + иконки сердец
        lives_label = self.hud_font.render(
            f"Жизни: {self.lives}", True, config.COLOR_WHITE
        )
        icons_width = config.INITIAL_LIVES * 24 + 8
        lives_panel_w = lives_label.get_width() + icons_width + 34
        lives_rect = pygame.Rect(20, 16, lives_panel_w, 46)
        self._draw_hud_panel(lives_rect)

        label_y = lives_rect.centery - lives_label.get_height() // 2
        self.screen.blit(lives_label, (lives_rect.x + 16, label_y))

        icons_start_x = lives_rect.x + 16 + lives_label.get_width() + 20
        for idx in range(config.INITIAL_LIVES):
            self._draw_life_icon(
                (icons_start_x + idx * 24, lives_rect.centery - 1),
                active=idx < self.lives,
            )

        # Правая панель: Очки
        score_prefix = self.hud_font.render(
            "Очки: ", True, config.COLOR_HUD_LABEL
        )
        score_value = self.hud_font.render(
            str(self.score), True, config.COLOR_HUD_SCORE
        )
        score_panel_w = (
            score_prefix.get_width() + score_value.get_width() + 36
        )
        score_rect = pygame.Rect(
            config.SCREEN_WIDTH - score_panel_w - 20, 16, score_panel_w, 46
        )
        self._draw_hud_panel(score_rect)

        score_y = score_rect.centery - score_prefix.get_height() // 2
        self.screen.blit(score_prefix, (score_rect.x + 18, score_y))
        self.screen.blit(
            score_value,
            (score_rect.x + 18 + score_prefix.get_width(), score_y),
        )

    def _render(self) -> None:
        """Отрисовать текущий кадр игры."""
        # Неподвижный фон и бесшовный динамический фон
        self.screen.blit(self.assets.background, (0, 0))
        offset = int(self.debris_offset_x)
        self.screen.blit(self.assets.debris, (offset, 0))
        self.screen.blit(self.assets.debris, (offset - config.SCREEN_WIDTH, 0))

        if self.in_game:
            for asteroid in self.asteroids:
                asteroid.draw(self.screen)
            for missile in self.missiles:
                missile.draw(self.screen)
            self.ship.draw(self.screen)
            for explosion in self.explosions:
                explosion.draw(self.screen)
        else:
            self.screen.blit(self.assets.splash, self.splash_rect)

        self._draw_hud()
        pygame.display.flip()

    def run(self) -> None:
        """Запустить главный игровой цикл до закрытия окна."""
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()