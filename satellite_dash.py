import numpy as np
from panda3d.core import CardMaker, NodePath, TransparencyAttrib

from node import Node


class SatelliteDash(Node):
    def __init__(
        self,
        loader,
        parent,
        name,
        earth,
        lat,
        long,
        sprite_size=1,
    ):
        super().__init__(name)

        self.sprite_size = sprite_size
        self.earth = earth  # Привязка к модели Земли
        self.lat = lat  # Широта
        self.long = 180 - long  # Долгота

        self.setup_sprite(loader, parent)

    def position(self):
        r = self.earth.radius + self.sprite_size / 3

        long = self.long - self.earth.angle

        x = (
            r * np.cos(np.radians(self.lat)) * np.sin(np.radians(long))
            + self.earth.model.getX()
        )
        y = (
            r * np.cos(np.radians(self.lat)) * np.cos(np.radians(long))
            + self.earth.model.getY()
        )
        z = r * np.sin(np.radians(self.lat)) + self.earth.model.getZ()

        return x, y, z

    def setup_sprite(self, loader, parent):
        # Создаем CardMaker для создания спрайта
        cm = CardMaker("sprite")
        coord = self.sprite_size / 2
        cm.set_frame(-coord, coord, -coord, coord)  # Размеры спрайта

        # Создаем NodePath для спрайта
        sprite_node = cm.generate()
        self.sprite = NodePath(sprite_node)

        # Загружаем текстуру для спрайта
        texture = loader.load_texture("models\sprites\satellite-dash.png")
        self.sprite.set_texture(texture)

        # Устанавливаем прозрачность
        self.sprite.set_transparency(TransparencyAttrib.M_alpha)

        # Прикрепляем спрайт к сцене
        self.sprite.reparent_to(parent)

        # Устанавливаем позицию спрайта относительно сцены
        x, y, z = self.position()
        self.sprite.set_pos(x, y, z)

        # Применяем эффект билборда, чтобы спрайт всегда был повернут к камере
        self.sprite.set_billboard_point_eye()

        # Отключаем освещение для спрайта
        self.sprite.setLightOff()

    def update(self, task):
        x, y, z = self.position()
        self.sprite.set_pos(x, y, z)
        return task.again

    @property
    def pos(self) -> tuple:
        return self.sprite.getX(), self.sprite.getY(), self.sprite.getZ()
