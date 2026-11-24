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


def _draw_radial_glow(
    surface: pygame.Surface,
    center: tuple[int, int],
    max_radius: int,
    color: tuple[int, int, int],
    peak_alpha: int,
    steps: int = 24,
) -> None:
    """Отрисовать мягкое радиальное свечение без резких границ."""
    glow = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)
    red, green, blue = color
    for step in range(steps, 0, -1):
        ratio = step / steps
        radius = max(1, int(max_radius * ratio))
        # Квадратичное затухание прозрачности от центра к краю
        alpha = max(1, int(peak_alpha * ((1.0 - ratio) ** 1.6 + 0.08) / steps))
        pygame.draw.circle(
            glow,
            (red, green, blue, min(255, alpha)),
            (max_radius, max_radius),
            radius,
        )
    surface.blit(glow, (center[0] - max_radius, center[1] - max_radius))


def _build_background() -> pygame.Surface:
    """Сгенерировать глубокий космический фон с мягкими туманностями."""
    width = config.SCREEN_WIDTH
    height = config.SCREEN_HEIGHT
    surface = pygame.Surface((width, height))

    # Плавный вертикальный градиент ночного космоса
    for y_pos in range(height):
        t_val = y_pos / max(1, height - 1)
        red = int(6 + 10 * math.sin(t_val * math.pi))
        green = int(8 + 6 * math.sin(t_val * math.pi))
        blue = int(20 + 18 * math.sin(t_val * math.pi))
        pygame.draw.line(
            surface, (red, green, blue), (0, y_pos), (width, y_pos)
        )

    rng = random.Random(2026)

    # Мягкие многослойные туманности
    nebula_palette = [
        (35, 95, 175),
        (115, 40, 155),
        (155, 48, 82),
        (24, 125, 150),
        (60, 55, 165),
    ]
    for _ in range(18):
        cx = rng.randint(-60, width + 60)
        cy = rng.randint(-60, height + 60)
        radius = rng.randint(150, 310)
        color = rng.choice(nebula_palette)
        peak = rng.randint(36, 68)
        _draw_radial_glow(surface, (cx, cy), radius, color, peak, steps=26)

    # Далёкие мелкие звёзды
    for _ in range(280):
        x_pos = rng.randint(0, width - 1)
        y_pos = rng.randint(0, height - 1)
        shade = rng.randint(110, 210)
        surface.set_at((x_pos, y_pos), (shade, shade, min(255, shade + 25)))

    # Средние цветные звёзды
    star_tints = [
        (240, 245, 255),
        (185, 220, 255),
        (255, 232, 195),
        (255, 200, 215),
    ]
    for _ in range(75):
        x_pos = rng.randint(4, width - 5)
        y_pos = rng.randint(4, height - 5)
        tint = rng.choice(star_tints)
        rad = 1 if rng.random() < 0.72 else 2
        pygame.draw.circle(surface, tint, (x_pos, y_pos), rad)

    # Яркие звёзды с ореолом и лучами дифракции
    bright_stars = [
        (int(width * 0.22), int(height * 0.28), (140, 205, 255), 38),
        (int(width * 0.74), int(height * 0.34), (255, 215, 165), 32),
        (int(width * 0.58), int(height * 0.72), (165, 225, 255), 46),
    ]
    for sx, sy, s_color, glow_r in bright_stars:
        _draw_radial_glow(surface, (sx, sy), glow_r, s_color, 130, steps=18)
        flare = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        mid = glow_r
        pygame.draw.line(
            flare, (*s_color, 110), (mid - 22, mid), (mid + 22, mid), 1
        )
        pygame.draw.line(
            flare, (*s_color, 110), (mid, mid - 22), (mid, mid + 22), 1
        )
        surface.blit(flare, (sx - mid, sy - mid))
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 3)

    return surface.convert()


def _build_debris() -> pygame.Surface:
    """Сгенерировать полупрозрачный слой космических обломков и пыли."""
    surface = pygame.Surface(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
    )
    rng = random.Random(101)

    for _ in range(42):
        cx = rng.randint(20, config.SCREEN_WIDTH - 20)
        cy = rng.randint(20, config.SCREEN_HEIGHT - 20)
        radius = rng.randint(4, 11)
        points = []
        vertices = 7
        for idx in range(vertices):
            ang = 2 * math.pi * idx / vertices
            dist = radius * rng.uniform(0.68, 1.05)
            points.append(
                (cx + math.cos(ang) * dist, cy + math.sin(ang) * dist)
            )
        shade = rng.randint(105, 150)
        base_color = (shade, shade + 2, shade + 12, config.DEBRIS_ALPHA)
        pygame.draw.polygon(surface, base_color, points)
        highlight = (
            min(255, shade + 35),
            min(255, shade + 38),
            min(255, shade + 48),
            int(config.DEBRIS_ALPHA * 0.65),
        )
        pygame.draw.circle(
            surface,
            highlight,
            (cx - radius // 3, cy - radius // 3),
            max(1, radius // 3),
        )

    # Лёгкая звёздная пыль для эффекта параллакса
    for _ in range(60):
        px = rng.randint(0, config.SCREEN_WIDTH - 1)
        py = rng.randint(0, config.SCREEN_HEIGHT - 1)
        pygame.draw.circle(
            surface, (190, 215, 255, 70), (px, py), rng.choice([1, 1, 2])
        )

    return surface


def _build_ship_sheet() -> pygame.Surface:
    """Сгенерировать треугольный тайл-лист корабля (2 кадра, 2x сглаживание)."""
    size = config.SHIP_TILE_SIZE
    scale = 2
    hi_size = size * scale
    sheet = pygame.Surface((hi_size * 2, hi_size), pygame.SRCALPHA)
    cy = hi_size // 2

    for tile_idx in range(2):
        cx = tile_idx * hi_size + hi_size // 2

        # Второй тайл: трёхслойное пламя и мягкое свечение двигателя
        if tile_idx == 1:
            _draw_radial_glow(
                sheet, (cx - 48, cy), 44, (255, 130, 35), 185, steps=16
            )
            outer_flame = [
                (cx - 28, cy - 15),
                (cx - 88, cy),
                (cx - 28, cy + 15),
            ]
            mid_flame = [
                (cx - 28, cy - 9),
                (cx - 72, cy),
                (cx - 28, cy + 9),
            ]
            core_flame = [
                (cx - 28, cy - 4),
                (cx - 54, cy),
                (cx - 28, cy + 4),
            ]
            pygame.draw.polygon(sheet, (255, 92, 24), outer_flame)
            pygame.draw.polygon(sheet, (255, 204, 64), mid_flame)
            pygame.draw.polygon(sheet, (255, 252, 224), core_flame)

        # Сопло двигателя в хвостовом вырезе треугольника
        nozzle = [
            (cx - 22, cy - 14),
            (cx - 38, cy - 10),
            (cx - 38, cy + 10),
            (cx - 22, cy + 14),
        ]
        pygame.draw.polygon(sheet, (46, 56, 78), nozzle)
        pygame.draw.polygon(sheet, (110, 128, 158), nozzle, 2)

        # Объёмный треугольный корпус (верхняя светлая и нижняя теневая грани)
        upper_hull = [
            (cx + 72, cy),
            (cx - 48, cy - 52),
            (cx - 26, cy),
        ]
        lower_hull = [
            (cx + 72, cy),
            (cx - 26, cy),
            (cx - 48, cy + 52),
        ]
        pygame.draw.polygon(sheet, (232, 240, 252), upper_hull)
        pygame.draw.polygon(sheet, (172, 186, 212), lower_hull)

        # Тёмные бронепанели внутри крыльев
        upper_panel = [
            (cx + 12, cy - 16),
            (cx - 38, cy - 40),
            (cx - 26, cy - 13),
        ]
        lower_panel = [
            (cx + 12, cy + 16),
            (cx - 38, cy + 40),
            (cx - 26, cy + 13),
        ]
        pygame.draw.polygon(sheet, (68, 84, 114), upper_panel)
        pygame.draw.polygon(sheet, (52, 66, 94), lower_panel)

        # Голубые акцентные полосы вдоль кромок крыльев
        pygame.draw.line(
            sheet, (70, 215, 255), (cx + 10, cy - 16), (cx - 38, cy - 40), 3
        )
        pygame.draw.line(
            sheet, (50, 180, 230), (cx + 10, cy + 16), (cx - 38, cy + 40), 3
        )

        # Чёткий внешний контур и световой блик на верхней кромке
        hull_outline = [
            (cx + 72, cy),
            (cx - 48, cy - 52),
            (cx - 26, cy),
            (cx - 48, cy + 52),
        ]
        pygame.draw.polygon(sheet, (40, 52, 76), hull_outline, 3)
        pygame.draw.line(
            sheet, (255, 255, 255), (cx + 68, cy - 1), (cx - 44, cy - 49), 2
        )

        # Острый цветовой акцент на носу корабля
        nose_accent = [
            (cx + 72, cy),
            (cx + 46, cy - 11),
            (cx + 52, cy),
            (cx + 46, cy + 11),
        ]
        pygame.draw.polygon(sheet, (70, 215, 255), nose_accent)

        # Гранёная кабина пилота со стеклянным бликом
        canopy_frame = [
            (cx + 34, cy),
            (cx + 2, cy - 13),
            (cx - 16, cy),
            (cx + 2, cy + 13),
        ]
        canopy_glass = [
            (cx + 28, cy),
            (cx + 2, cy - 9),
            (cx - 11, cy),
            (cx + 2, cy + 9),
        ]
        canopy_glint = [
            (cx + 20, cy - 1),
            (cx + 3, cy - 6),
            (cx - 4, cy - 2),
            (cx + 6, cy - 1),
        ]
        pygame.draw.polygon(sheet, (22, 38, 66), canopy_frame)
        pygame.draw.polygon(sheet, (58, 205, 255), canopy_glass)
        pygame.draw.polygon(sheet, (225, 250, 255), canopy_glint)

    return pygame.transform.smoothscale(sheet, (size * 2, size))


def _build_asteroid() -> pygame.Surface:
    """Сгенерировать объёмный спрайт астероида с кратерами и сглаживанием."""
    size = config.ASTEROID_SIZE
    scale = 2
    hi_size = size * scale
    surface = pygame.Surface((hi_size, hi_size), pygame.SRCALPHA)
    center = hi_size // 2
    base_r = config.ASTEROID_RADIUS * scale
    rng = random.Random(19)

    points = []
    inner_points = []
    vertices = 15
    for idx in range(vertices):
        ang = 2 * math.pi * idx / vertices
        dist = base_r * rng.uniform(0.84, 1.03)
        points.append(
            (center + math.cos(ang) * dist, center + math.sin(ang) * dist)
        )
        inner_points.append(
            (
                center - 6 + math.cos(ang) * dist * 0.84,
                center - 6 + math.sin(ang) * dist * 0.84,
            )
        )

    pygame.draw.polygon(surface, (112, 114, 126), points)
    pygame.draw.polygon(surface, (148, 150, 162), inner_points)
    pygame.draw.polygon(surface, (68, 70, 82), points, 5)

    # Объёмные кратеры с тенью и светлым ободком
    craters = [(-22, -18, 18), (24, -10, 14), (-8, 26, 16), (16, 22, 10)]
    for dx, dy, rad in craters:
        pos = (center + dx, center + dy)
        pygame.draw.circle(surface, (92, 94, 106), pos, rad)
        pygame.draw.circle(
            surface,
            (132, 134, 146),
            (pos[0] + 2, pos[1] + 2),
            max(2, rad - 3),
        )
        pygame.draw.circle(surface, (74, 76, 88), pos, rad, 2)

    return pygame.transform.smoothscale(surface, (size, size))


def _build_missile() -> pygame.Surface:
    """Сгенерировать светящийся энергетический снаряд (ракету)."""
    size = 24
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    _draw_radial_glow(
        surface, (center, center), 11, (255, 110, 40), 210, steps=8
    )
    pygame.draw.circle(surface, (255, 225, 120), (center, center), 5)
    pygame.draw.circle(surface, (255, 255, 240), (center, center), 3)
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
                sheet, (225, 68, 22, alpha), (cx, center), outer_r
            )
        if inner_r > 2:
            pygame.draw.circle(
                sheet,
                (255, 178, 48, alpha),
                (cx, center),
                int(outer_r * 0.72),
            )
            pygame.draw.circle(
                sheet, (255, 250, 210, alpha), (cx, center), inner_r
            )

        # Разлетающиеся искры
        for ray in range(10):
            angle = ray * math.pi / 5 + progress * 0.7
            dist = outer_r * 0.92 + progress * 16
            sx = int(cx + math.cos(angle) * dist)
            sy = int(center + math.sin(angle) * dist)
            pygame.draw.circle(sheet, (255, 210, 95, alpha), (sx, sy), 3)

    return sheet


def _build_splash() -> pygame.Surface:
    """Сгенерировать стартовую заставку игры на русском языке."""
    width = config.SPLASH_WIDTH
    height = config.SPLASH_HEIGHT
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Тёмная полупрозрачная карточка со скруглёнными углами
    pygame.draw.rect(
        surface, (12, 18, 42, 218), surface.get_rect(), border_radius=20
    )
    pygame.draw.rect(
        surface,
        config.COLOR_SPLASH_BORDER,
        surface.get_rect(),
        width=3,
        border_radius=20,
    )

    title_font = pygame.font.SysFont(config.UI_FONT_NAME, 52, bold=True)
    btn_font = pygame.font.SysFont(config.UI_FONT_NAME, 22, bold=True)
    hint_font = pygame.font.SysFont(config.UI_FONT_NAME, 16)

    # Заголовок с тенью
    shadow_surf = title_font.render("АСТЕРОИДЫ", True, (10, 14, 30))
    title_surf = title_font.render("АСТЕРОИДЫ", True, config.COLOR_WHITE)
    title_center = (width // 2, 78)
    shadow_rect = shadow_surf.get_rect(
        center=(title_center[0] + 3, title_center[1] + 3)
    )
    surface.blit(shadow_surf, shadow_rect)
    surface.blit(title_surf, title_surf.get_rect(center=title_center))

    # Кнопка старта внутри заставки
    btn_rect = pygame.Rect(0, 0, 310, 54)
    btn_rect.center = (width // 2, 164)
    pygame.draw.rect(surface, (36, 118, 225), btn_rect, border_radius=12)
    pygame.draw.rect(
        surface, (145, 210, 255), btn_rect, width=2, border_radius=12
    )
    btn_surf = btn_font.render("НАЖМИТЕ ДЛЯ СТАРТА", True, config.COLOR_WHITE)
    surface.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))

    # Подсказка по управлению
    hint_text = "← → поворот   •   ↑ двигатель   •   Пробел — огонь"
    hint_surf = hint_font.render(hint_text, True, (180, 200, 232))
    surface.blit(
        hint_surf, hint_surf.get_rect(center=(width // 2, height - 42))
    )

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

    ship_sheet = (
        _load_image_if_exists("double_ship.png") or _build_ship_sheet()
    )
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