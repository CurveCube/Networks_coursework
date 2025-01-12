import numpy as np
import panda3d.core as p3d
import simplepbr
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, LVector3
from json import load

from camera_controller import CameraController
from earth import Earth
from network import Network
from satellite import Satellite, Calculator
from satellite_dash import SatelliteDash
from skybox import Skybox

p3d.load_prc_file_data(
    "",
    "window-size 1024 768\n"
    "texture-minfilter mipmap\n"
    "texture-anisotropic-degree 16\n",
)

CONFIG_PATH = "config.json"


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
        with open(CONFIG_PATH, "r") as f:
            config = load(f)

        self.earth.time_factor = config["time_factor"]

        # Настройка управления камерой
        self.camera_controller = CameraController(
            self.camera, self.taskMgr, self.mouseWatcherNode, self.center, config["camera_rotation_angle"], config["camera_rotation_angle_vertical"], config["camera_radius"]
        )

        # Отключение управления мышью по умолчанию
        self.disable_mouse()

        # Установка обработчиков событий мыши
        self.accept("mouse1", self.camera_controller.start_rotation)
        self.accept("mouse1-up", self.camera_controller.stop_rotation)
        self.accept("wheel_up", self.camera_controller.zoom_in)
        self.accept("wheel_down", self.camera_controller.zoom_out)
        self.accept("arrow_up", self.increase_time_factor)
        self.accept("arrow_down", self.decrease_time_factor)

        # Установка спутников
        self.setup_satellites(config)

        # Установка станций
        self.setup_satellite_dashes(config)

        # Установка топологии сети
        self.network = Network(
            self.central_node,
            self.earth,
            self.satellites,
            self.dashes,
            f"d_{config['sender']}",
            f"d_{config['recipient']}",
            config['update_topology_interval'],
            config["dash_cone_angle"],
            tuple(config["path_color"]),
            config["path_thickness"],
        )

        self.taskMgr.add(self.network.update, "update_network")

    def increase_time_factor(self):
        self.earth.time_factor *= 10
        self.calculator.time_factor = self.calculator.time_factor * 10

    def decrease_time_factor(self):
        self.earth.time_factor /= 10
        self.calculator.time_factor = self.calculator.time_factor / 10

    def setup_satellites(self, config):
        self.satellites = []
        sprite_size = config["sprite_size"]
        time_factor = config["time_factor"]
        self.calculator = Calculator(time_factor)
        num_orbit_segments = config["num_orbit_segments"]
        orbit_color = tuple(config["orbit_color"])
        orbit_thickness = config["orbit_thickness"]
        for i, satellite_info in enumerate(config["satellites"]):
            satellite = Satellite(
                self.loader,
                self.central_node,
                self.earth_pos,
                f"s_{i}",
                calculator=self.calculator,
                a=satellite_info["a"],
                e=satellite_info["e"],
                i=np.radians(satellite_info["i"]),
                omega=np.radians(satellite_info["omega"]),
                w=np.radians(satellite_info["w"]),
                m=np.radians(satellite_info["m"]),
                sprite_size=sprite_size,
                num_orbit_segments=num_orbit_segments,
                line_color=orbit_color,
                line_thickness=orbit_thickness
            )
            self.satellites.append(satellite)
        self.calculator.update_position()
        self.taskMgr.add(self.update_satellites, "update_satellites")

    def update_satellites(self, task):
        self.calculator.update_position()
        for satellite in self.satellites:
            satellite.update()
        return task.again

    def setup_satellite_dashes(self, config):
        self.dashes = []
        sprite_size = config["sprite_size"]
        for i, dash_info in enumerate(config["dashes"]):
            dash = SatelliteDash(
                self.loader, self.central_node, f"d_{i}", self.earth, dash_info["lat"], dash_info["long"], sprite_size
            )
            self.dashes.append(dash)
            self.taskMgr.add(dash.update, f"update_dash_{i}")

    def close(self):
        self.network.timer.cancel()
        print("close")


def main():
    app = App()
    try:
        app.run()
    except:
        app.close()


if __name__ == "__main__":
    main()
