"""ООП-иерархия игровых сущностей и физическая модель игры «Астероиды»."""

import math
import random

import pygame

from src import config


def angle_to_vector(angle_deg: float) -> tuple[float, float]:
    """Преобразовать угол ориентации в единичный вектор направления.

    В системе координат экрана ось Y направлена вниз, а pygame.transform.rotate
    выполняет поворот против часовой стрелки. Поэтому компонента Y берётся
    с обратным знаком: (cos(rad), -sin(rad)).

    Args:
        angle_deg: Угол поворота в градусах (0 градусов — вправо).

    Returns:
        Кортеж (dx, dy) единичной длины.
    """
    rad = math.radians(angle_deg)
    return math.cos(rad), -math.sin(rad)


class GameObject:
    """Базовый игровой объект на тороидальном двумерном поле."""

    def __init__(
        self,
        pos: tuple[float, float],
        vel: tuple[float, float],
        angle: float,
        angle_vel: float,
        radius: float,
        image: pygame.Surface,
    ) -> None:
        """Инициализировать базовые физические и визуальные свойства объекта.

        Args:
            pos: Начальные координаты центра (x, y).
            vel: Начальная линейная скорость (vx, vy) в пикселях/с.
            angle: Начальный угол ориентации в градусах.
            angle_vel: Угловая скорость в градусах/с.
            radius: Радиус окружного хитбокса.
            image: Текущий спрайт объекта.
        """
        self.pos = [float(pos[0]), float(pos[1])]
        self.vel = [float(vel[0]), float(vel[1])]
        self.angle = float(angle)
        self.angle_vel = float(angle_vel)
        self.radius = float(radius)
        self.image = image

    def update(self, dt: float) -> None:
        """Обновить положение и угол объекта с учётом тороидальной геометрии.

        При выходе за любую границу экрана координата берётся по модулю
        соответствующего размера поля, сохраняя линейную и угловую скорости.

        Args:
            dt: Длительность кадра в секундах.
        """
        self.pos[0] = (self.pos[0] + self.vel[0] * dt) % config.SCREEN_WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1] * dt) % config.SCREEN_HEIGHT
        self.angle = (self.angle + self.angle_vel * dt) % 360.0

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовать спрайт объекта с поворотом вокруг его центра.

        Args:
            surface: Целевая поверхность экрана.
        """
        rotated = pygame.transform.rotate(self.image, self.angle)
        rect = rotated.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        surface.blit(rotated, rect)

    def collides_with(self, other: "GameObject") -> bool:
        """Проверить столкновение с другим объектом по радиусам хитбоксов.

        Учитывается кратчайшее расстояние на тороидальной поверхности:
        объекты у противоположных краёв поля также корректно сталкиваются.

        Args:
            other: Второй игровой объект.

        Returns:
            True, если объекты пересекаются, иначе False.
        """
        dx = abs(self.pos[0] - other.pos[0])
        dy = abs(self.pos[1] - other.pos[1])
        # Кратчайшее расстояние через границы тора
        dx = min(dx, config.SCREEN_WIDTH - dx)
        dy = min(dy, config.SCREEN_HEIGHT - dy)
        distance = math.hypot(dx, dy)
        return distance < (self.radius + other.radius)


class Missile(GameObject):
    """Ракета, летящая с постоянной скоростью и ограниченным временем жизни."""

    def __init__(
        self,
        pos: tuple[float, float],
        vel: tuple[float, float],
        angle: float,
        image: pygame.Surface,
    ) -> None:
        """Создать ракету в точке выстрела.

        Args:
            pos: Начальные координаты (нос корабля).
            vel: Постоянный вектор скорости (vx, vy).
            angle: Угол ориентации ракеты.
            image: Спрайт ракеты.
        """
        super().__init__(
            pos=pos,
            vel=vel,
            angle=angle,
            angle_vel=0.0,
            radius=config.MISSILE_RADIUS,
            image=image,
        )
        self.age = 0.0
        self.lifespan = config.MISSILE_LIFESPAN

    def update(self, dt: float) -> bool:
        """Обновить положение ракеты и проверить истечение времени жизни.

        Args:
            dt: Длительность кадра в секундах.

        Returns:
            True, если время жизни ракеты истекло и её нужно удалить.
        """
        super().update(dt)
        self.age += dt
        return self.age >= self.lifespan


class Ship(GameObject):
    """Управляемый корабль игрока с тайловой сменой состояния двигателя."""

    def __init__(
        self,
        tiles: list[pygame.Surface],
        missile_image: pygame.Surface,
    ) -> None:
        """Создать корабль в центре игрового поля.

        Args:
            tiles: Список из двух тайлов [без тяги, с включённым двигателем].
            missile_image: Спрайт выпускаемых ракет.
        """
        self._tiles = tiles
        self._missile_image = missile_image
        self.thrust = False
        center = (config.SCREEN_WIDTH / 2.0, config.SCREEN_HEIGHT / 2.0)
        super().__init__(
            pos=center,
            vel=(0.0, 0.0),
            angle=0.0,
            angle_vel=0.0,
            radius=config.SHIP_RADIUS,
            image=self._tiles[0],
        )

    def set_thrust(self, active: bool) -> None:
        """Включить или выключить маршевый двигатель корабля.

        Args:
            active: True — двигатель включён, False — выключен.
        """
        self.thrust = active
        self.image = self._tiles[1] if active else self._tiles[0]

    def set_rotation(self, direction: int) -> None:
        """Задать направление вращения корабля вокруг своего центра.

        Args:
            direction: +1 — против часовой (влево), -1 — по часовой (вправо),
                0 — остановка вращения.
        """
        self.angle_vel = direction * config.SHIP_ANGULAR_SPEED

    def reset(self) -> None:
        """Возродить корабль неподвижным в центре игрового поля."""
        self.pos = [config.SCREEN_WIDTH / 2.0, config.SCREEN_HEIGHT / 2.0]
        self.vel = [0.0, 0.0]
        self.angle = 0.0
        self.angle_vel = 0.0
        self.set_thrust(False)

    def update(self, dt: float) -> None:
        """Обновить скорость, тягу, сопротивление среды и позицию корабля.

        Args:
            dt: Длительность кадра в секундах.
        """
        if self.thrust:
            # Ускорение строго по вектору ориентации корабля
            fx, fy = angle_to_vector(self.angle)
            self.vel[0] += fx * config.SHIP_THRUST_ACCEL * dt
            self.vel[1] += fy * config.SHIP_THRUST_ACCEL * dt

            # Ограничение максимальной скорости для комфортного управления
            speed = math.hypot(self.vel[0], self.vel[1])
            if speed > config.SHIP_MAX_SPEED:
                scale = config.SHIP_MAX_SPEED / speed
                self.vel[0] *= scale
                self.vel[1] *= scale
        else:
            # Экспоненциальное затухание скорости из-за сопротивления среды
            damping = math.exp(-config.SHIP_DRAG_COEFF * dt)
            self.vel[0] *= damping
            self.vel[1] *= damping
            if math.hypot(self.vel[0], self.vel[1]) < config.SHIP_STOP_EPSILON:
                self.vel = [0.0, 0.0]

        super().update(dt)

    def shoot(self) -> Missile:
        """Выпустить ракету из носа корабля по направлению его ориентации.

        Returns:
            Новый экземпляр класса Missile.
        """
        fx, fy = angle_to_vector(self.angle)
        nose_pos = (
            (self.pos[0] + fx * self.radius) % config.SCREEN_WIDTH,
            (self.pos[1] + fy * self.radius) % config.SCREEN_HEIGHT,
        )
        missile_vel = (fx * config.MISSILE_SPEED, fy * config.MISSILE_SPEED)
        return Missile(
            pos=nose_pos,
            vel=missile_vel,
            angle=self.angle,
            image=self._missile_image,
        )


class Asteroid(GameObject):
    """Астероид со случайной линейной и угловой скоростью."""

    @classmethod
    def spawn_random(
        cls,
        image: pygame.Surface,
        avoid_pos: tuple[float, float],
    ) -> "Asteroid":
        """Создать астероид в случайной точке поля на безопасном расстоянии.

        Args:
            image: Спрайт астероида.
            avoid_pos: Координаты корабля, рядом с которым нельзя появляться.

        Returns:
            Новый экземпляр класса Asteroid.
        """
        pos = (0.0, 0.0)
        for _ in range(25):
            cand_x = random.uniform(0.0, config.SCREEN_WIDTH)
            cand_y = random.uniform(0.0, config.SCREEN_HEIGHT)
            if math.hypot(cand_x - avoid_pos[0], cand_y - avoid_pos[1]) >= (
                config.ASTEROID_SAFE_SPAWN_DIST
            ):
                pos = (cand_x, cand_y)
                break

        move_angle = random.uniform(0.0, 2.0 * math.pi)
        speed = random.uniform(
            config.ASTEROID_MIN_SPEED, config.ASTEROID_MAX_SPEED
        )
        vel = (math.cos(move_angle) * speed, math.sin(move_angle) * speed)
        angle = random.uniform(0.0, 360.0)
        angle_vel = random.uniform(
            -config.ASTEROID_MAX_ANG_SPEED, config.ASTEROID_MAX_ANG_SPEED
        )

        return cls(
            pos=pos,
            vel=vel,
            angle=angle,
            angle_vel=angle_vel,
            radius=config.ASTEROID_RADIUS,
            image=image,
        )


class Explosion(GameObject):
    """Тайловая анимация взрыва на месте уничтоженного астероида."""

    def __init__(
        self,
        pos: tuple[float, float],
        frames: list[pygame.Surface],
    ) -> None:
        """Создать анимацию взрыва в заданной точке.

        Args:
            pos: Координаты центра взрыва (x, y).
            frames: Список тайлов анимации взрыва.
        """
        self._frames = frames
        self._elapsed = 0.0
        super().__init__(
            pos=pos,
            vel=(0.0, 0.0),
            angle=0.0,
            angle_vel=0.0,
            radius=0.0,
            image=self._frames[0],
        )

    def update(self, dt: float) -> bool:
        """Переключить текущий тайл взрыва в зависимости от прошедшего времени.

        Args:
            dt: Длительность кадра в секундах.

        Returns:
            True, если все кадры проиграны и анимацию можно удалить.
        """
        self._elapsed += dt
        frame_index = int(self._elapsed * config.EXPLOSION_FPS)
        if frame_index >= len(self._frames):
            return True
        self.image = self._frames[frame_index]
        return False