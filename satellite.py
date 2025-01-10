import time

import numpy as np
from panda3d.core import CardMaker, LineSegs, LPoint3, NodePath, TransparencyAttrib

from node import Node


class Satellite(Node):
    def __init__(
        self,
        loader,
        parent,
        pos_shift,
        name,
        a,
        e,
        i,
        omega,
        w,
        m,
        mu=398600.4418,
        sprite_size=1,
        num_orbit_segments=1000,
        line_color=(1, 1, 1, 0.8),
        line_thickness=1.5,
        time_factor=100,
    ):
        super().__init__(name)

        self.sprite_size = sprite_size
        self.num_orbit_segments = num_orbit_segments
        self.line_color = line_color
        self.line_thickness = line_thickness

        self.pos_shift = pos_shift

        self.t0 = time.time()
        self.time_factor = time_factor

        self.a = a  # Большая полуось в тыс.км
        self.e = e  # Эксцентриситет
        self.i = i  # Наклонение орбиты
        self.omega = omega  # Долгота восходящего узла
        self.w = w  # Аргумент перицентра
        self.m = m  # Средняя аномалия
        self.mu = mu  # Гравитационный параметр в км^3/с^2

        self.setup_sprite(loader, parent)
        self.setup_orbit(parent)

    def mean_motion(self):
        return np.sqrt(self.mu / (self.a * 1000) ** 3)

    def mean_anomaly(self, delta_t):
        n = self.mean_motion()
        return self.m + n * delta_t

    def eccentric_anomaly(self, M):
        E = M
        for _ in range(10):  # Метод Ньютона для решения уравнения Кеплера
            E_next = E + (M - E + self.e * np.sin(E)) / (1 - self.e * np.cos(E))
            if abs(E_next - E) < 1e-8:
                break
            E = E_next
        return E

    def true_anomaly(self, E):
        return 2 * np.arctan2(
            np.sqrt(1 - self.e) * np.cos(E / 2), np.sqrt(1 + self.e) * np.sin(E / 2)
        )

    def radius(self, E):
        return self.a * (1 - self.e * np.cos(E))

    def position(self, delta_t):
        M = self.mean_anomaly(delta_t)
        E = self.eccentric_anomaly(M)
        nu = self.true_anomaly(E)
        r = self.radius(E)

        x_orb = r * np.cos(nu)
        y_orb = r * np.sin(nu)

        # Вычисление координат в экваториальной плоскости
        x_eq = x_orb * (
            np.cos(self.omega) * np.cos(self.w)
            - np.sin(self.omega) * np.sin(self.w) * np.cos(self.i)
        ) - y_orb * (
            np.cos(self.omega) * np.sin(self.w)
            + np.sin(self.omega) * np.cos(self.w) * np.cos(self.i)
        )
        y_eq = x_orb * (
            np.sin(self.omega) * np.cos(self.w)
            + np.cos(self.omega) * np.sin(self.w) * np.cos(self.i)
        ) + y_orb * (
            -np.sin(self.omega) * np.sin(self.w)
            + np.cos(self.omega) * np.cos(self.w) * np.cos(self.i)
        )
        z_eq = x_orb * np.sin(self.i) * np.sin(self.w) + y_orb * np.sin(
            self.i
        ) * np.cos(self.w)

        return x_eq, y_eq, z_eq

    def _orbit(self):
        rad = np.linspace(0, 2 * np.pi, self.num_orbit_segments + 1)
        orbit = []
        for M in rad:
            E = self.eccentric_anomaly(M)
            nu = self.true_anomaly(E)
            r = self.radius(E)

            x_orb = r * np.cos(nu)
            y_orb = r * np.sin(nu)

            # Вычисление координат в экваториальной плоскости
            x_eq = x_orb * (
                np.cos(self.omega) * np.cos(self.w)
                - np.sin(self.omega) * np.sin(self.w) * np.cos(self.i)
            ) - y_orb * (
                np.cos(self.omega) * np.sin(self.w)
                + np.sin(self.omega) * np.cos(self.w) * np.cos(self.i)
            )
            y_eq = x_orb * (
                np.sin(self.omega) * np.cos(self.w)
                + np.cos(self.omega) * np.sin(self.w) * np.cos(self.i)
            ) + y_orb * (
                -np.sin(self.omega) * np.sin(self.w)
                + np.cos(self.omega) * np.cos(self.w) * np.cos(self.i)
            )
            z_eq = x_orb * np.sin(self.i) * np.sin(self.w) + y_orb * np.sin(
                self.i
            ) * np.cos(self.w)
            orbit.append((x_eq, y_eq, z_eq))
        return orbit

    def setup_orbit(self, parent):
        # Создаем LineSegs для рисования орбиты
        ls = LineSegs()
        ls.set_color(*self.line_color)
        ls.set_thickness(self.line_thickness)  # Толщина линии

        # Рисуем эллипс
        orbit_points = self._orbit()
        for x, y, z in orbit_points:
            ls.draw_to(LPoint3(x, y, z))

        # Создаем NodePath для орбиты
        orbit_node = ls.create()
        self.orbit = NodePath(orbit_node)

        # Отключаем освещение для орбиты
        self.orbit.setLightOff()

        # Прикрепляем орбиту к сцене
        self.orbit.reparent_to(parent)

        # Устанавливаем позицию орбиты относительно сцены
        self.orbit.set_pos(*self.pos_shift)

    def setup_sprite(self, loader, parent):
        # Создаем CardMaker для создания спрайта
        cm = CardMaker("sprite")
        coord = self.sprite_size / 2
        cm.set_frame(-coord, coord, -coord, coord)  # Размеры спрайта

        # Создаем NodePath для спрайта
        sprite_node = cm.generate()
        self.sprite = NodePath(sprite_node)

        # Загружаем текстуру для спрайта
        texture = loader.load_texture("models\sprites\satellite.png")
        self.sprite.set_texture(texture)

        # Устанавливаем прозрачность
        self.sprite.set_transparency(TransparencyAttrib.M_alpha)

        # Прикрепляем спрайт к сцене
        self.sprite.reparent_to(parent)

        # Устанавливаем позицию спрайта относительно сцены
        x, y, z = self.position(0.0)
        print("satellite coords: ", x, y, z)
        self.sprite.set_pos(
            x + self.pos_shift[0], y + self.pos_shift[1], z + self.pos_shift[2]
        )

        # Применяем эффект билборда, чтобы спрайт всегда был повернут к камере
        self.sprite.set_billboard_point_eye()

        # Отключаем освещение для спрайта
        self.sprite.setLightOff()

    def update(self, task):
        t = time.time()
        delta_t = (self.t0 - t) * self.time_factor
        x, y, z = self.position(delta_t)
        self.sprite.set_pos(
            x + self.pos_shift[0], y + self.pos_shift[1], z + self.pos_shift[2]
        )
        return task.again

    @property
    def pos(self) -> tuple:
        return self.sprite.getX(), self.sprite.getY(), self.sprite.getZ()
