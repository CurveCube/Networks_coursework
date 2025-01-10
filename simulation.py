import numpy as np
import panda3d.core as p3d
import simplepbr
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, LVector3

from camera_controller import CameraController
from earth import Earth
from network import Network
from satellite import Satellite
from satellite_dash import SatelliteDash
from skybox import Skybox

p3d.load_prc_file_data(
    "",
    "window-size 1024 768\n"
    "texture-minfilter mipmap\n"
    "texture-anisotropic-degree 16\n",
)


class App(ShowBase):
    def __init__(self):
        super().__init__()
        self.pipeline = simplepbr.init()

        self.incline = 23.5  # Наклон оси вращения Земли
        self.center = 0, 0, 0
        self.earth_pos = 0, 0, 0

        # Фиктивный узел, который задает наклон и расположение остальных объектов
        self.central_node = self.render.attachNewNode("central_node")
        self.central_node.setPos(*self.center)
        self.central_node.setR(self.incline)

        # Установка модели Земли
        self.setup_earth()

        # Установка окружения
        self.setup_skybox()

        # Установка освещения
        self.setup_lights()

        # Загрузка конфигурации
        self.load_config()

    def setup_earth(self):
        self.earth = Earth(self.loader)
        self.earth.model.reparentTo(self.central_node)
        self.earth.model.setPos(*self.earth_pos)
        self.taskMgr.add(self.earth.update, "update_earth")

    def setup_skybox(self):
        self.skybox = Skybox(self.loader)
        self.skybox.model.reparentTo(self.central_node)

    def setup_lights(self):
        # Создание фонового света
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.015, 0.015, 0.015, 1))
        ambientLightNode = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNode)

        # Создание направленного света
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((LVector3(1, 0, 0)))
        directionalLight.setColor((5, 5, 5, 1))
        self.directionalLightNode = self.render.attachNewNode(directionalLight)
        self.render.setLight(self.directionalLightNode)

    def load_config(self):
        self.earth.time_factor = 1000

        # Настройка управления камерой
        self.camera_controller = CameraController(
            self.camera, self.taskMgr, self.mouseWatcherNode, self.center
        )

        # Отключение управления мышью по умолчанию
        self.disable_mouse()

        # Установка обработчиков событий мыши
        self.accept("mouse1", self.camera_controller.start_rotation)
        self.accept("mouse1-up", self.camera_controller.stop_rotation)
        self.accept("wheel_up", self.camera_controller.zoom_in)
        self.accept("wheel_down", self.camera_controller.zoom_out)

        # Установка спутников
        self.setup_satellites()

        # Установка станций
        self.setup_satellite_dashes()

        # Установка топологии сети
        self.network = Network(
            self.central_node,
            self.earth,
            self.satellites,
            self.dashes,
            "dash1",
            "dash2",
        )

        self.taskMgr.add(self.network.update, "update_network")

    def setup_satellites(self):
        self.satellites = [
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite1",
                a=40,
                e=0.7,
                i=np.radians(30),
                omega=np.radians(45),
                w=np.radians(90),
                m=np.radians(358),
                time_factor=1000,
            ),
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite2",
                a=40,
                e=0.7,
                i=np.radians(30),
                omega=np.radians(45),
                w=np.radians(60),
                m=np.radians(270),
                time_factor=1000,
            ),
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite3",
                a=10,
                e=0.1,
                i=np.radians(-57),
                omega=np.radians(50),
                w=np.radians(0),
                m=np.radians(0),
                time_factor=1000,
            ),
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite4",
                a=6.5,
                e=0,
                i=np.radians(0),
                omega=np.radians(0),
                w=np.radians(30),
                m=np.radians(0),
                time_factor=1000,
            ),
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite5",
                a=6.5,
                e=0,
                i=np.radians(90),
                omega=np.radians(90),
                w=np.radians(0),
                m=np.radians(0),
                time_factor=1000,
            ),
            Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                "satellite6",
                a=6.5,
                e=0,
                i=np.radians(90),
                omega=np.radians(0),
                w=np.radians(0),
                m=np.radians(50),
                time_factor=1000,
            ),
        ]
        for i, satellite in enumerate(self.satellites):
            self.taskMgr.add(satellite.update, f"update_satellite_{i}")

    def setup_satellite_dashes(self):
        self.dashes = [
            SatelliteDash(
                self.loader, self.central_node, "dash1", self.earth, 59.57, 30.19
            ),
            SatelliteDash(
                self.loader, self.central_node, "dash2", self.earth, 40.42, -74.00
            ),
        ]
        for i, dash in enumerate(self.dashes):
            self.taskMgr.add(dash.update, f"update_dash_{i}")


def main():
    App().run()


if __name__ == "__main__":
    main()
