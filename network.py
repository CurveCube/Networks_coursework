import networkx as nx
import numpy as np
from networkx.algorithms.shortest_paths.generic import shortest_path
from panda3d.core import LineSegs, LPoint3, NodePath
import time


class Network:
    def __init__(
        self,
        parent,
        earth,
        satellites,
        dashes,
        sender,
        recipient,
        dash_cone_angle=60,
        path_color=(0, 1, 0, 0.8),
        path_thickness=1.5,
    ):
        self.parent = parent
        self.earth = earth

        self.lines = []
        self.graph = nx.Graph()
        self.sender = sender
        self.recipient = recipient
        self.path = []

        self.path_color = path_color
        self.path_thickness = path_thickness

        self.dash_cone_cos2 = np.cos(np.radians(dash_cone_angle)) ** 2

        self.satellites = {}
        for satellite in satellites:
            self.satellites[satellite.id] = satellite
            self.graph.add_node(satellite.id)

        self.dashes = {}
        for dash in dashes:
            self.dashes[dash.id] = dash
            self.graph.add_node(dash.id)

    def weight(self, node1, node2, attrs):
        if node1 in self.dashes:
            p1 = self.dashes[node1].pos
            p2 = self.satellites[node2].pos
        elif node2 in self.dashes:
            p1 = self.dashes[node2].pos
            p2 = self.satellites[node1].pos
        else:
            p1 = self.satellites[node1].pos
            p2 = self.satellites[node2].pos
        weight = (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
        return weight

    def get_shortest_path(self):
        try:
            return shortest_path(self.graph, self.sender, self.recipient, self.weight)
        except:
            return []

    def _update(self):
        for line in self.lines:
            line.remove_node()
        self.graph.clear_edges()

        self.lines = []
        processed = set()
        for dash_id, dash in self.dashes.items():
            for satellite_id, satellite in self.satellites.items():
                p1 = dash.pos
                p2 = satellite.pos
                cos2 = ((p2[0] - p1[0]) * (p1[0] - self.earth.model.getX()) + (p2[1] - p1[1]) * (p1[1] - self.earth.model.getY()) + (p2[1] - p1[1]) * (p1[2] - self.earth.model.getZ())) ** 2 / (
                    (p1[0] - self.earth.model.getX()) ** 2 + (p1[1] - self.earth.model.getY()) ** 2 + (p1[2] - self.earth.model.getZ()) ** 2
                ) / (
                    (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
                )
                if cos2 > self.dash_cone_cos2:
                    self.graph.add_edge(dash_id, satellite_id)
        for cur_satellite_id, cur_satellite in self.satellites.items():
            for satellite_id, satellite in self.satellites.items():
                if cur_satellite_id == satellite_id or satellite_id in processed:
                    continue

                p1 = cur_satellite.pos
                p2 = satellite.pos
                e1 = np.sqrt(
                    (p1[0] - self.earth.model.getX()) ** 2
                    + (p1[1] - self.earth.model.getY()) ** 2
                    + (p1[2] - self.earth.model.getZ()) ** 2
                )
                e2 = np.sqrt(
                    (p2[0] - self.earth.model.getX()) ** 2
                    + (p2[1] - self.earth.model.getY()) ** 2
                    + (p2[2] - self.earth.model.getZ()) ** 2
                )
                e3 = np.sqrt(
                    (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2
                )
                p = (e1 + e2 + e3) / 2
                h = 2 * np.sqrt(p * (p - e1) * (p - e2) * (p - e3)) / e3
                if h > self.earth.radius:
                    self.graph.add_edge(cur_satellite_id, satellite_id)
            processed.add(cur_satellite_id)

        self.path = self.get_shortest_path()
        #print("path: ", self.path)
        if len(self.path) < 2:
            return

        ls = LineSegs()
        ls.set_color(*self.path_color)
        ls.set_thickness(self.path_thickness)

        points = []
        for i in range(len(self.path)):
            if i == 0 or i == len(self.path) - 1:
                p = self.dashes[self.path[i]].pos
            else:
                p = self.satellites[self.path[i]].pos
            points.append(p)

        # Рисуем путь
        for x, y, z in points:
            ls.draw_to(LPoint3(x, y, z))

        # Создаем NodePath для пути
        node = ls.create()
        line = NodePath(node)

        # Отключаем освещение для пути
        line.setLightOff()

        # Прикрепляем путь к сцене
        line.reparent_to(self.parent)

        # Устанавливаем позицию пути относительно сцены
        line.set_pos(self.earth.model.getPos())

        self.lines.append(line)

    def update(self, task):
        self._update()
        return task.again
