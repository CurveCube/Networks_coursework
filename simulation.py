import math
import os

import panda3d.core as p3d
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Shader
from panda3d.core import AmbientLight, DirectionalLight, PointLight, Spotlight
from panda3d.core import CardMaker, NodePath, TransparencyAttrib, DepthTestAttrib, RenderAttrib, BillboardEffect
from panda3d.core import LineSegs, LPoint3, LVector3

import simplepbr

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

        # Загрузка модели GLTF
        try:
            self.model = self.loader.loadModel("models/earth/earth.gltf")
            self.model.reparentTo(self.render)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")

        # Загрузка окружения
        try:
            self.skybox_cubemap = self.loader.loadCubeMap("models/skybox/face_#.png")
            self.skybox = self.loader.loadModel("models/skybox/skybox.egg")
            self.skybox.reparentTo(self.render)
            self.skybox.setShader(Shader.load(Shader.SLGLSL, "shaders/skybox_vert.glsl", "shaders/skybox_frag.glsl"))
            self.skybox.setShaderInput("TexSkybox", self.skybox_cubemap)
            self.skybox.setAttrib(DepthTestAttrib.make(RenderAttrib.MLessEqual))
            self.skybox.setLightOff()
            print("Skybox loaded successfully")
        except Exception as e:
            print(f"Error loading skybox: {e}")

        # Установка модели
        self.model.setPos(0, 0, 0)
        self.model.setScale(7)

        # Установка камеры
        self.camera.setPos(0, -40, 0)  # Отодвиньте камеру дальше
        self.camera.lookAt(0, 0, 0)

        # Перемещение освещения из модели в рендер
        self.model.clear_light()
        for light in self.model.find_all_matches('**/+Light'):
            light.parent.wrt_reparent_to(self.render)
            self.render.set_light(light)

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


        self.setup_sprite()
        self.setup_orbit()

    def setup_orbit(self):
        # Создаем LineSegs для рисования орбиты
        ls = LineSegs()
        ls.set_color(1, 1, 1, 1)  # Белый цвет
        ls.set_thickness(2)  # Толщина линии

        # Количество сегментов для круга
        num_segments = 1000
        radius = 10  # Радиус орбиты

        # Рисуем круг
        for i in range(num_segments + 1):
            angle = 2 * 3.14159 * i / num_segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            ls.draw_to(LPoint3(x, y, 0))

        # Создаем NodePath для орбиты
        orbit_node = ls.create()
        orbit = NodePath(orbit_node)

        # Прикрепляем орбиту к сцене
        orbit.reparent_to(self.render)

        # Устанавливаем позицию орбиты относительно сцены
        orbit.set_pos(0, 0, 0)  # Позиция орбиты в сцене

    def setup_sprite(self):
        # Создаем CardMaker для создания спрайта
        cm = CardMaker("sprite")
        cm.set_frame(-1, 1, -1, 1)  # Размеры спрайта

        # Создаем NodePath для спрайта
        sprite_node = cm.generate()
        sprite = NodePath(sprite_node)

        # Загружаем текстуру для спрайта
        texture = self.loader.load_texture("models\sprites\satellite.png")
        sprite.set_texture(texture)

        # Устанавливаем прозрачность
        sprite.set_transparency(TransparencyAttrib.M_alpha)

        # Прикрепляем спрайт к сцене
        sprite.reparent_to(self.render)

        # Устанавливаем позицию спрайта относительно сцены
        sprite.set_pos(10, 0, 0)  # Позиция спрайта в сцене
        sprite.set_scale(0.5)  # Масштаб спрайта

        # Применяем эффект билборда, чтобы спрайт всегда был повернут к камере
        sprite.set_billboard_point_eye()


    def setup_lights(self):
        # Создание фонового света
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.2, 0.2, 0.2, 1))
        ambientLightNode = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNode)

        # Создание направленного света
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((LVector3(0, 1, 0)))
        directionalLight.setColor((0.9, 0.9, 0.9, 1))
        directionalLightNode = self.render.attachNewNode(directionalLight)
        self.render.setLight(directionalLightNode)

        '''# Создание точечного света
        pointLight = PointLight("pointLight")
        pointLight.setColor((1, 1, 1, 1))
        pointLight.setAttenuation((1, 0, 0))
        pointLightNode = self.render.attachNewNode(pointLight)
        pointLightNode.setPos(0, 0, 10)
        self.render.setLight(pointLightNode)

        # Создание прожекторного света
        spotlight = Spotlight("spotlight")
        spotlight.setColor((1, 1, 1, 1))
        spotlight.setAttenuation((1, 0, 0))
        spotlightNode = self.render.attachNewNode(spotlight)
        spotlightNode.setPos(0, 0, 10)
        spotlightNode.lookAt(0, 0, 0)
        self.render.setLight(spotlightNode)'''

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