"""Глобальные параметры и константы игры «Астероиды»."""

from pathlib import Path

# Пути к ресурсам
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

# Параметры окна и игрового цикла
WINDOW_TITLE = "Астероиды"
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

# Начальное состояние игры
INITIAL_LIVES = 3
INITIAL_SCORE = 0

# Параметры динамического фона (движется влево с постоянной скоростью)
DEBRIS_SCROLL_SPEED = 45.0  # пикселей в секунду
DEBRIS_ALPHA = 115          # полупрозрачность слоя (0..255)

# Параметры корабля
SHIP_TILE_SIZE = 96
SHIP_RADIUS = 32.0
SHIP_ANGULAR_SPEED = 210.0  # градусов в секунду
SHIP_THRUST_ACCEL = 420.0   # пикселей / с^2
SHIP_MAX_SPEED = 380.0      # ограничение максимальной скорости (пикселей / с)
SHIP_DRAG_COEFF = 1.4       # коэффициент сопротивления среды при выкл. тяге
SHIP_STOP_EPSILON = 5.0     # порог полной остановки корабля (пикселей / с)

# Параметры ракет
MISSILE_RADIUS = 6.0
MISSILE_SPEED = 560.0       # постоянная скорость ракеты (пикселей / с)
# Ракета не может пролететь поле целиком даже по малой стороне (75% от min)
MISSILE_MAX_DISTANCE = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.75
MISSILE_LIFESPAN = MISSILE_MAX_DISTANCE / MISSILE_SPEED

# Параметры астероидов
ASTEROID_SIZE = 88
ASTEROID_RADIUS = 38.0
ASTEROID_SPAWN_INTERVAL = 1.25    # интервал генерации астероидов (секунды)
ASTEROID_MAX_COUNT = 12           # максимум астероидов на поле одновременно
ASTEROID_MIN_SPEED = 55.0         # минимальная линейная скорость (пикс / с)
ASTEROID_MAX_SPEED = 165.0        # максимальная линейная скорость (пикс / с)
ASTEROID_MAX_ANG_SPEED = 120.0    # максимальная угловая скорость (град / с)
ASTEROID_SAFE_SPAWN_DIST = 160.0  # безопасная дистанция от корабля

# Параметры тайловой анимации взрыва
EXPLOSION_TILE_SIZE = 128
EXPLOSION_FRAME_COUNT = 24
EXPLOSION_FPS = 36.0

# Параметры прямоугольника заставки
SPLASH_WIDTH = 500
SPLASH_HEIGHT = 290

# Шрифт с поддержкой кириллицы на macOS / Windows / Linux
UI_FONT_NAME = "helveticaneue,arial,dejavusans"

# Цвета интерфейса (RGB / RGBA)
COLOR_WHITE = (245, 248, 255)
COLOR_HUD_BG = (10, 14, 28, 205)
COLOR_HUD_BORDER = (80, 175, 255)
COLOR_HUD_LABEL = (195, 215, 240)
COLOR_HUD_SCORE = (255, 215, 75)
COLOR_LIFE_ACTIVE = (255, 82, 98)
COLOR_LIFE_LOST = (55, 65, 88)
COLOR_SPLASH_BORDER = (85, 175, 255)