"""Загрузка, процедурная генерация и нарезка тайловых спрайтов."""

from dataclasses import dataclass
import math
import random

import pygame

from src import config


def slice_tile_sheet(
    sheet: pygame.Surface,
    tile_width: int,
    tile_height: int,
    count: int,
) -> list[pygame.Surface]:
    """Нарезать горизонтальный тайл-лист на отдельные кадры.

    Args:
        sheet: Исходное изображение, содержащее кадры в один ряд.
        tile_width: Ширина одного тайла в пикселях.
        tile_height: Высота одного тайла в пикселях.
        count: Количество кадров в листе.

    Returns:
        Список поверхностей Pygame, соответствующих отдельным кадрам.
    """
    frames: list[pygame.Surface] = []
    for index in range(count):
        rect = pygame.Rect(index * tile_width, 0, tile_width, tile_height)
        frame = sheet.subsurface(rect).copy()
        frames.append(frame)
    return frames


@dataclass
class GameAssets:
    """Контейнер со всеми графическими ресурсами и тайлами игры."""

    background: pygame.Surface
    debris: pygame.Surface
    splash: pygame.Surface
    ship_tiles: list[pygame.Surface]
    asteroid: pygame.Surface
    missile: pygame.Surface
    explosion_frames: list[pygame.Surface]


def _load_image_if_exists(
    filename: str,
    size: tuple[int, int] | None = None,
) -> pygame.Surface | None:
    """Загрузить изображение из папки assets, если файл существует."""
    path = config.ASSETS_DIR / filename
    if not path.is_file():
        return None
    image = pygame.image.load(str(path)).convert_alpha()
    if size is not None:
        image = pygame.transform.smoothscale(image, size)
    return image


def _build_background() -> pygame.Surface:
    """Сгенерировать неподвижный космический фон с туманностью и звёздами."""
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    surface.fill((12, 10, 24))
    rng = random.Random(42)

    # Полупрозрачные облака туманности
    nebula_colors = [
        (110, 35, 25, 22),
        (55, 30, 115, 22),
        (25, 65, 115, 18),
    ]
    for _ in range(32):
        radius = rng.randint(70, 190)
        blob = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            blob, rng.choice(nebula_colors), (radius, radius), radius
        )
        pos = (
            rng.randint(-radius, config.SCREEN_WIDTH - radius),
            rng.randint(-radius, config.SCREEN_HEIGHT - radius),
        )
        surface.blit(blob, pos)

    # Звёзды
    for _ in range(220):
        x = rng.randint(0, config.SCREEN_WIDTH - 1)
        y = rng.randint(0, config.SCREEN_HEIGHT - 1)
        brightness = rng.randint(150, 255)
        star_radius = 1 if rng.random() < 0.85 else 2
        pygame.draw.circle(
            surface, (brightness, brightness, 255), (x, y), star_radius
        )

    return surface.convert()


def _build_debris() -> pygame.Surface:
    """Сгенерировать полупрозрачный динамический слой мелких астероидов."""
    surface = pygame.Surface(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
    )
    rng = random.Random(101)

    for _ in range(55):
        cx = rng.randint(15, config.SCREEN_WIDTH - 15)
        cy = rng.randint(15, config.SCREEN_HEIGHT - 15)
        radius = rng.randint(4, 13)
        points = []
        vertices = 7
        for idx in range(vertices):
            ang = 2 * math.pi * idx / vertices
            dist = radius * rng.uniform(0.65, 1.05)
            points.append(
                (cx + math.cos(ang) * dist, cy + math.sin(ang) * dist)
            )
        shade = rng.randint(120, 175)
        color = (shade, shade - 10, shade - 20, config.DEBRIS_ALPHA)
        pygame.draw.polygon(surface, color, points)

    return surface


def _build_ship_sheet() -> pygame.Surface:
    """Сгенерировать тайл-лист корабля (2 тайла: без тяги и с двигателем)."""
    size = config.SHIP_TILE_SIZE
    sheet = pygame.Surface((size * 2, size), pygame.SRCALPHA)
    half = size // 2

    # Корабль ориентирован вправо (угол 0 градусов)
    hull = [
        (half + 32, half),
        (half - 24, half - 24),
        (half - 12, half),
        (half - 24, half + 24),
    ]

    for tile_idx in range(2):
        offset_x = tile_idx * size
        shifted_hull = [(x + offset_x, y) for x, y in hull]

        # На втором тайле рисуем пламя работающего двигателя
        if tile_idx == 1:
            outer_flame = [
                (offset_x + half - 14, half - 11),
                (offset_x + half - 42, half),
                (offset_x + half - 14, half + 11),
            ]
            inner_flame = [
                (offset_x + half - 15, half - 6),
                (offset_x + half - 31, half),
                (offset_x + half - 15, half + 6),
            ]
            pygame.draw.polygon(sheet, (255, 120, 20), outer_flame)
            pygame.draw.polygon(sheet, (255, 240, 110), inner_flame)

        pygame.draw.polygon(sheet, (205, 215, 230), shifted_hull)
        pygame.draw.polygon(sheet, (90, 110, 140), shifted_hull, 2)
        # Кабина пилота
        pygame.draw.ellipse(
            sheet, (70, 190, 255), (offset_x + half - 2, half - 6, 16, 12)
        )

    return sheet


def _build_asteroid() -> pygame.Surface:
    """Сгенерировать спрайт астероида с неровным контуром и кратерами."""
    size = config.ASTEROID_SIZE
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    base_r = config.ASTEROID_RADIUS
    rng = random.Random(7)

    points = []
    vertices = 14
    for idx in range(vertices):
        ang = 2 * math.pi * idx / vertices
        dist = base_r * rng.uniform(0.84, 1.04)
        points.append(
            (center + math.cos(ang) * dist, center + math.sin(ang) * dist)
        )

    pygame.draw.polygon(surface, (145, 145, 152), points)
    pygame.draw.polygon(surface, (85, 85, 92), points, 3)

    # Кратеры
    craters = [(-11, -9, 9), (12, -5, 7), (-4, 13, 8), (8, 12, 5)]
    for dx, dy, rad in craters:
        pos = (center + dx, center + dy)
        pygame.draw.circle(surface, (112, 112, 118), pos, rad)
        pygame.draw.circle(surface, (90, 90, 96), pos, rad, 1)

    return surface


def _build_missile() -> pygame.Surface:
    """Сгенерировать спрайт ракеты."""
    size = 18
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    pygame.draw.circle(surface, (255, 90, 40, 160), (center, center), 8)
    pygame.draw.circle(surface, (255, 245, 160), (center, center), 4)
    return surface


def _build_explosion_sheet() -> pygame.Surface:
    """Сгенерировать 24-кадровый тайл-лист анимации взрыва."""
    size = config.EXPLOSION_TILE_SIZE
    count = config.EXPLOSION_FRAME_COUNT
    sheet = pygame.Surface((size * count, size), pygame.SRCALPHA)
    center = size // 2

    for idx in range(count):
        # Нормализованный прогресс анимации t in [0.0, 1.0]
        progress = idx / max(1, count - 1)
        alpha = int(255 * (1.0 - progress) ** 0.85)
        outer_r = int(12 + (center - 10) * math.sin(progress * math.pi * 0.85))
        inner_r = max(2, int(outer_r * (1.0 - progress * 0.55)))
        cx = idx * size + center

        if outer_r > 2:
            pygame.draw.circle(
                sheet, (220, 65, 20, alpha), (cx, center), outer_r
            )
        if inner_r > 2:
            pygame.draw.circle(
                sheet,
                (255, 175, 45, alpha),
                (cx, center),
                int(outer_r * 0.72),
            )
            pygame.draw.circle(
                sheet, (255, 250, 200, alpha), (cx, center), inner_r
            )

        # Разлетающиеся искры
        for ray in range(8):
            angle = ray * math.pi / 4 + progress * 0.6
            dist = outer_r * 0.95 + progress * 14
            sx = int(cx + math.cos(angle) * dist)
            sy = int(center + math.sin(angle) * dist)
            pygame.draw.circle(sheet, (255, 200, 80, alpha), (sx, sy), 3)

    return sheet


def _build_splash() -> pygame.Surface:
    """Сгенерировать стартовую заставку игры по центру экрана."""
    surface = pygame.Surface(
        (config.SPLASH_WIDTH, config.SPLASH_HEIGHT), pygame.SRCALPHA
    )
    surface.fill((30, 35, 110, 175))
    pygame.draw.rect(
        surface,
        config.COLOR_SPLASH_BORDER,
        surface.get_rect(),
        width=4,
    )

    title_font = pygame.font.SysFont("arial", 54, bold=True)
    sub_font = pygame.font.SysFont("arial", 24, bold=True)

    title_surf = title_font.render("ASTEROIDS", True, config.COLOR_WHITE)
    sub_surf = sub_font.render("CLICK TO START", True, (180, 220, 255))

    title_rect = title_surf.get_rect(
        center=(config.SPLASH_WIDTH // 2, config.SPLASH_HEIGHT // 2 - 28)
    )
    sub_rect = sub_surf.get_rect(
        center=(config.SPLASH_WIDTH // 2, config.SPLASH_HEIGHT // 2 + 38)
    )
    surface.blit(title_surf, title_rect)
    surface.blit(sub_surf, sub_rect)
    return surface


def load_assets() -> GameAssets:
    """Загрузить графику из assets/ или сгенерировать тайл-листы программно.

    Returns:
        Заполненный экземпляр GameAssets.
    """
    background = _load_image_if_exists(
        "nebula.png", (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    ) or _build_background()

    debris = _load_image_if_exists(
        "debris.png", (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    ) or _build_debris()

    splash = _load_image_if_exists(
        "splash.png", (config.SPLASH_WIDTH, config.SPLASH_HEIGHT)
    ) or _build_splash()

    ship_sheet = _load_image_if_exists("double_ship.png") or _build_ship_sheet()
    ship_tile_w = ship_sheet.get_width() // 2
    ship_tile_h = ship_sheet.get_height()
    ship_tiles = slice_tile_sheet(ship_sheet, ship_tile_w, ship_tile_h, 2)

    asteroid = _load_image_if_exists(
        "asteroid.png", (config.ASTEROID_SIZE, config.ASTEROID_SIZE)
    ) or _build_asteroid()

    missile = _load_image_if_exists("shot.png") or _build_missile()

    explosion_sheet = (
        _load_image_if_exists("explosion.png") or _build_explosion_sheet()
    )
    exp_tile_w = explosion_sheet.get_width() // config.EXPLOSION_FRAME_COUNT
    exp_tile_h = explosion_sheet.get_height()
    explosion_frames = slice_tile_sheet(
        explosion_sheet,
        exp_tile_w,
        exp_tile_h,
        config.EXPLOSION_FRAME_COUNT,
    )

    return GameAssets(
        background=background,
        debris=debris,
        splash=splash,
        ship_tiles=ship_tiles,
        asteroid=asteroid,
        missile=missile,
        explosion_frames=explosion_frames,
    )