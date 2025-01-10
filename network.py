import networkx as nx
import numpy as np
from networkx.algorithms.shortest_paths.generic import shortest_path
from panda3d.core import LineSegs, LPoint3, NodePath


class Network:
    def __init__(
        self,
        parent,
        earth,
        satellites,
        dashes,
        sender,
        recipient,
        lines_color=(0.5, 0.5, 0.5, 0.5),
        path_color=(0, 1, 0, 0.8),
        lines_thickness=1.5,
        path_thickness=1.5,
    ):
        self.parent = parent
        self.earth = earth

        self.lines = []
        self.graph = nx.Graph()
        self.sender = sender
        self.recipient = recipient
        self.path = []

        self.lines_color = lines_color
        self.lines_thickness = lines_thickness
        self.path_color = path_color
        self.path_thickness = path_thickness

        self.satellites = {}
        for satellite in satellites:
            self.satellites[satellite.name] = satellite
            self.graph.add_node(satellite.name)

        self.dashes = {}
        for dash in dashes:
            self.dashes[dash.name] = dash
            self.graph.add_node(dash.name)

    def weight(self, node1, node2, attrs):
        if node1 in self.dashes:
            p1 = self.dashes[node1].pos
        else:
            p1 = self.satellites[node1].pos
        if node2 in self.dashes:
            p2 = self.dashes[node2].pos
        else:
            p2 = self.satellites[node2].pos
        return np.sqrt(
            (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
        )

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
        for dash_name, dash in self.dashes.items():
            for satellite_name, satellite in self.satellites.items():
                p1 = dash.pos
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
                    ls = LineSegs()
                    ls.set_color(*self.lines_color)
                    ls.set_thickness(self.lines_thickness)

                    # Рисуем отрезок
                    for x, y, z in [p1, p2]:
                        ls.draw_to(LPoint3(x, y, z))

                    # Создаем NodePath для отрезка
                    node = ls.create()
                    line = NodePath(node)

                    # Отключаем освещение для отрезка
                    line.setLightOff()

                    # Прикрепляем отрезок к сцене
                    line.reparent_to(self.parent)

                    # Устанавливаем позицию отрезка относительно сцены
                    line.set_pos(self.earth.model.getPos())
                    self.lines.append(line)
                    self.graph.add_edge(dash_name, satellite_name)
        for cur_satellite_name, cur_satellite in self.satellites.items():
            for satellite_name, satellite in self.satellites.items():
                if cur_satellite_name == satellite_name or satellite_name in processed:
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
                    ls = LineSegs()
                    ls.set_color(*self.lines_color)
                    ls.set_thickness(self.lines_thickness)

                    # Рисуем отрезок
                    for x, y, z in [p1, p2]:
                        ls.draw_to(LPoint3(x, y, z))

                    # Создаем NodePath для отрезка
                    node = ls.create()
                    line = NodePath(node)

                    # Отключаем освещение для отрезка
                    line.setLightOff()

                    # Прикрепляем отрезок к сцене
                    line.reparent_to(self.parent)

                    # Устанавливаем позицию отрезка относительно сцены
                    line.set_pos(self.earth.model.getPos())
                    self.lines.append(line)
                    self.graph.add_edge(cur_satellite_name, satellite_name)
            processed.add(cur_satellite_name)

        self.path = self.get_shortest_path()
        if len(self.path) < 2:
            return

        for i in range(len(self.path) - 1):
            if i == 0:
                p1 = self.dashes[self.path[i]].pos
                p2 = self.satellites[self.path[i + 1]].pos
            elif i == len(self.path) - 2:
                p1 = self.satellites[self.path[i]].pos
                p2 = self.dashes[self.path[i + 1]].pos
            else:
                p1 = self.satellites[self.path[i]].pos
                p2 = self.satellites[self.path[i + 1]].pos
            ls = LineSegs()
            ls.set_color(*self.path_color)
            ls.set_thickness(self.path_thickness)

            # Рисуем отрезок
            for x, y, z in [p1, p2]:
                ls.draw_to(LPoint3(x, y, z))

            # Создаем NodePath для отрезка
            node = ls.create()
            line = NodePath(node)

            # Отключаем освещение для отрезка
            line.setLightOff()

            # Прикрепляем отрезок к сцене
            line.reparent_to(self.parent)

            # Устанавливаем позицию отрезка относительно сцены
            line.set_pos(self.earth.model.getPos())

            self.lines.append(line)

    def update(self, task):
        self._update()
        return task.again
