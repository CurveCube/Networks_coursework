import math
import os

import panda3d.core as p3d
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Shader
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import CardMaker, NodePath, TransparencyAttrib, DepthTestAttrib, RenderAttrib, BillboardEffect
from panda3d.core import LineSegs, LPoint3, LVector3

import simplepbr

from satellite import Satellite
from earth import Earth
import numpy as np
import time

p3d.load_prc_file_data(
    '',
    'window-size 1024 768\n'
    'texture-minfilter mipmap\n'
    'texture-anisotropic-degree 16\n'
)

class App(ShowBase):
    def __init__(self):
        super().__init__()
        self.pipeline = simplepbr.init()

        self.incline = 23.5 # Наклон оси вращения Земли
        self.center = 0, 0, 0

        # Фиктивный узел, который задает наклон и расположение остальных объектов
        self.central_node = self.render.attachNewNode("central_node")
        self.central_node.setPos(*self.center)
        self.central_node.setR(self.incline)

        # Загрузка конфигурации
        self.load_config()
        
        # Установка модели Земли
        self.setup_earth()

        # Загрузка окружения
        try:
            self.skybox_cubemap = self.loader.loadCubeMap("models/skybox/face_#.png")
            self.skybox = self.loader.loadModel("models/skybox/skybox.egg")
            self.skybox.reparentTo(self.central_node)
            self.skybox.setShader(Shader.load(Shader.SLGLSL, "shaders/skybox_vert.glsl", "shaders/skybox_frag.glsl"))
            self.skybox.setShaderInput("TexSkybox", self.skybox_cubemap)
            self.skybox.setAttrib(DepthTestAttrib.make(RenderAttrib.MLessEqual))
            self.skybox.setLightOff()
            print("Skybox loaded successfully")
        except Exception as e:
            print(f"Error loading skybox: {e}")

        # Установка камеры
        self.camera.setPos(0, -40, 0)  # Отодвиньте камеру дальше
        self.camera.lookAt(0, 0, 0)

        # Добавление освещения
        self.setup_lights()

        # Отключение управления мышью по умолчанию
        self.disable_mouse()

        #Может вынести в отдельный класс управление камерой?

        # Инициализация углов вращения
        self.rotation_angle = 0
        self.rotation_angle_vertical = 0

        # Инициализация радиуса орбиты камеры
        self.camera_radius = 40

        # Инициализация начальных позиций мыши
        self.mouse_start_x = None
        self.mouse_start_y = None

        # Установка обработчиков событий мыши
        self.accept("mouse1", self.start_rotation)
        self.accept("mouse1-up", self.stop_rotation)
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        self.setup_satellite()

    def load_config(self):
        self.time_factor = 1000

    def setup_earth(self):
        self.earth = Earth(self.loader, self.time_factor)
        self.earth.model.reparentTo(self.central_node)
        self.earth.model.setPos(*self.center)
        self.taskMgr.add(self.earth.update, "update_earth")

    def setup_satellite(self):
        self.satellites = [Satellite(a=40, e=0.7, i=np.radians(30), omega=np.radians(45), w=np.radians(60), m=np.radians(358)),
                           Satellite(a=40, e=0.7, i=np.radians(30), omega=np.radians(45), w=np.radians(60), m=np.radians(270)),
                           Satellite(a=10, e=0.1, i=np.radians(-57), omega=np.radians(50), w=np.radians(0), m=np.radians(0)),
                           Satellite(a=6.371, e=0, i=np.radians(0), omega=np.radians(0), w=np.radians(0), m=np.radians(0))]
        self.t0 = time.time()
        for satellite in self.satellites:
            x, y, z = satellite.position(self.t0, self.t0)
            print(x, y, z)
            satellite.sprite = self.setup_sprite(x, y, z)
            satellite.orbit = self.setup_orbit(satellite)
        self.taskMgr.add(self.update_satellite, "update_satellite")
        
    def update_satellite(self, task):
        t = time.time()
        delta_t = (self.t0 - t)
        for satellite in self.satellites:
            x, y, z = satellite.position(self.t0 + delta_t, self.t0)
            satellite.sprite.set_pos(x, y, z)
        return task.again

    def setup_orbit(self, satellite):
        # Создаем LineSegs для рисования орбиты
        ls = LineSegs()
        ls.set_color(1, 1, 1, 0.8)  # Белый цвет
        ls.set_thickness(1.5)  # Толщина линии

        # Количество сегментов для круга
        num_segments = 1000
        orbit_points = satellite.orbit(num_segments)

        # Рисуем круг
        for x, y, z in orbit_points:
            ls.draw_to(LPoint3(x, y, z))

        # Создаем NodePath для орбиты
        orbit_node = ls.create()
        orbit = NodePath(orbit_node)

        # Прикрепляем орбиту к сцене
        orbit.reparent_to(self.central_node)
        orbit.setLightOff()

        # Устанавливаем позицию орбиты относительно сцены
        orbit.set_pos(0, 0, 0)  # Позиция орбиты в сцене
        return orbit

    def setup_sprite(self, x, y ,z):
        # Создаем CardMaker для создания спрайта
        size = 0.5
        cm = CardMaker("sprite")
        cm.set_frame(-size, size, -size, size)  # Размеры спрайта

        # Создаем NodePath для спрайта
        sprite_node = cm.generate()
        sprite = NodePath(sprite_node)

        # Загружаем текстуру для спрайта
        texture = self.loader.load_texture("models\sprites\satellite.png")
        sprite.set_texture(texture)

        # Устанавливаем прозрачность
        sprite.set_transparency(TransparencyAttrib.M_alpha)

        # Прикрепляем спрайт к сцене
        sprite.reparent_to(self.central_node)

        # Устанавливаем позицию спрайта относительно сцены
        sprite.set_pos(x, y, z)  # Позиция спрайта в сцене

        # Применяем эффект билборда, чтобы спрайт всегда был повернут к камере
        sprite.set_billboard_point_eye()

        # Отключаем освещение для спрайта
        sprite.setLightOff()

        return sprite

    def setup_lights(self):
        # Создание фонового света
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.015, 0.015, 0.015, 1))
        ambientLightNode = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNode)

        # Создание направленного света
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((LVector3(0, 1, 0)))
        directionalLight.setColor((5, 5, 5, 1))
        self.directionalLightNode = self.render.attachNewNode(directionalLight)
        self.render.setLight(self.directionalLightNode)

    def start_rotation(self):
        # Сохранение начальной позиции мыши
        if self.mouseWatcherNode.hasMouse():
            self.mouse_start_x = self.mouseWatcherNode.getMouseX()
            self.mouse_start_y = self.mouseWatcherNode.getMouseY()
            # Запуск задачи для обновления позиции камеры
            self.taskMgr.add(self.update_camera, "update_camera")

    def stop_rotation(self):
        # Сброс начальной позиции мыши
        self.mouse_start_x = None
        self.mouse_start_y = None
        self.taskMgr.remove("update_camera")

    def zoom_in(self):
        # Увеличение радиуса орбиты камеры
        self.camera_radius *= 0.9

        # Вычисление новой позиции камеры
        radius = self.camera_radius  # Радиус орбиты камеры
        angleRadians = math.radians(self.rotation_angle)
        angleRadiansVertical = math.radians(self.rotation_angle_vertical)

        self.camera.setPos(radius * math.sin(angleRadians) * math.cos(angleRadiansVertical),
                            -radius * math.cos(angleRadians) * math.cos(angleRadiansVertical),
                            radius * math.sin(angleRadiansVertical))
        self.camera.lookAt(0, 0, 0)  # Направьте камеру на модель

    def zoom_out(self):
        # Уменьшение радиуса орбиты камеры
        self.camera_radius *= 1.1

        # Вычисление новой позиции камеры
        radius = self.camera_radius  # Радиус орбиты камеры
        angleRadians = math.radians(self.rotation_angle)
        angleRadiansVertical = math.radians(self.rotation_angle_vertical)

        self.camera.setPos(radius * math.sin(angleRadians) * math.cos(angleRadiansVertical),
                            -radius * math.cos(angleRadians) * math.cos(angleRadiansVertical),
                            radius * math.sin(angleRadiansVertical))
        self.camera.lookAt(0, 0, 0)  # Направьте камеру на модель

    def update_camera(self, task):
        # Обновление углов вращения на основе движения мыши
        if self.mouseWatcherNode.hasMouse() and self.mouse_start_x is not None and self.mouse_start_y is not None:
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()

            # Вычисление разницы позиций мыши
            delta_x = x - self.mouse_start_x
            delta_y = y - self.mouse_start_y

            # Обновление углов вращения
            self.rotation_angle += delta_x * 100
            self.rotation_angle_vertical += delta_y * 100

            # Ограничение вертикального угла вращения
            self.rotation_angle_vertical = max(min(self.rotation_angle_vertical, 80), -80)

            # Обновление начальной позиции мыши
            self.mouse_start_x = x
            self.mouse_start_y = y

            # Вычисление новой позиции камеры
            radius = self.camera_radius  # Радиус орбиты камеры
            angleRadians = math.radians(self.rotation_angle)
            angleRadiansVertical = math.radians(self.rotation_angle_vertical)

            self.camera.setPos(radius * math.sin(angleRadians) * math.cos(angleRadiansVertical),
                               -radius * math.cos(angleRadians) * math.cos(angleRadiansVertical),
                               radius * math.sin(angleRadiansVertical))
            self.camera.lookAt(0, 0, 0)  # Направьте камеру на модель

        return task.cont

def main():
    App().run()

if __name__ == '__main__':
    main()