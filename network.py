from threading import Timer

import networkx as nx
import numpy as np
from networkx.algorithms.shortest_paths.generic import shortest_path
from panda3d.core import LineSegs, LPoint3, NodePath

from message import MsgQueue
from protocol_srp import SRP_receiver, SRP_sender


class Network:
    def __init__(
        self,
        parent,
        earth,
        satellites,
        dashes,
        sending_interval=0.1,
        loss_probability=0.2,
        window_size=8,
        timeout=0.5,
        update_interval=0.5,
        dash_cone_angle=60,
        path_color=(0, 1, 0, 0.8),
        path_thickness=1.5,
    ):
        self.parent = parent
        self.earth = earth

        self.lines = []
        self.graph = nx.Graph()
        self.sender = None
        self.recipient = None
        self.path = []

        self.srp_sender = None
        self.srp_reciever = None
        self.send_msg_queue = None
        self.answer_msg_queue = None
        self.posted_msgs = None
        self.received_msgs = None

        self.set_progress_callback = None

        self.update_interval = update_interval
        self.sending_interval = sending_interval
        self.loss_probability = loss_probability
        self.window_size = window_size
        self.timeout = timeout

        self.path_color = path_color
        self.path_thickness = path_thickness

        self.dash_cone_cos2 = np.cos(np.radians(dash_cone_angle))

        self.satellites = {}
        for satellite in satellites:
            self.satellites[satellite.id] = satellite
            self.graph.add_node(satellite.id)

        self.dashes = {}
        for dash in dashes:
            self.dashes[dash.id] = dash
            self.graph.add_node(dash.id)

        self.topology_timer = Timer(self.update_interval, self.update_topology)
        self.topology_timer.start()

        self.sending_timer = None

    def send(self, sender, recipient, packages_count):
        if self.sending_timer:
            self.sending_timer.cancel()

        self.sender = f"d_{sender}"
        self.recipient = f"d_{recipient}"

        print(f"Start sending from {self.sender} to {self.recipient}")

        self.send_msg_queue = MsgQueue(self.loss_probability)
        self.answer_msg_queue = MsgQueue(self.loss_probability)
        self.posted_msgs = []
        self.received_msgs = []

        self.srp_sender = SRP_sender(
            self.answer_msg_queue,
            self.send_msg_queue,
            self.posted_msgs,
            self.window_size,
            packages_count,
            self.timeout,
        )
        self.srp_reciever = SRP_receiver(
            self.answer_msg_queue, self.send_msg_queue, self.received_msgs
        )

        if self.set_progress_callback:
            self.set_progress_callback(
                f"Packages: 0/{packages_count}.\nSended: {0}.\nReceived: {0}"
            )

        self.sending_timer = Timer(self.sending_interval, self._send)
        self.sending_timer.start()

    def _send(self):
        self.check_path()

        if len(self.path) > 0:
            self.srp_sender.send()
            self.srp_reciever.receive()
            if self.set_progress_callback:
                self.set_progress_callback(
                    f"Packages: {self.srp_sender.ans_count}/{self.srp_sender.max_number}.\nSended: {len(self.posted_msgs)}.\nReceived: {len(self.received_msgs)}"
                )

        if not self.srp_sender.is_finished():
            self.sending_timer = Timer(self.sending_interval, self._send)
            self.sending_timer.start()
        else:
            print(f"Sending from {self.sender} to {self.recipient} finished")
            print("Posted: ", len(self.posted_msgs))
            print("Recived: ", len(self.received_msgs))
            self.sender = None
            self.recipient = None
            self.srp_sender = None
            self.srp_reciever = None
            self.send_msg_queue = None
            self.answer_msg_queue = None
            self.posted_msgs = None
            self.received_msgs = None
            if self.set_progress_callback:
                self.set_progress_callback("")

    def close(self):
        self.topology_timer.cancel()
        if self.sending_timer:
            self.sending_timer.cancel()

    def update_topology(self):
        self.graph.clear_edges()

        processed = set()
        for dash_id, dash in self.dashes.items():
            for satellite_id, satellite in self.satellites.items():
                p1 = dash.pos
                p2 = satellite.pos
                e1 = [
                    p1[0] - self.earth.model.getX(),
                    p1[1] - self.earth.model.getY(),
                    p1[2] - self.earth.model.getZ(),
                ]
                e2 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
                cos2 = (e1[0] * e2[0] + e1[1] * e2[1] + e1[2] * e2[2]) / np.sqrt(
                    (e1[0] * e1[0] + e1[1] * e1[1] + e1[2] * e1[2])
                    * (e2[0] * e2[0] + e2[1] * e2[1] + e2[2] * e2[2])
                )
                if cos2 > self.dash_cone_cos2:
                    self.graph.add_edge(dash_id, satellite_id)
        for cur_satellite_id, cur_satellite in self.satellites.items():
            for satellite_id, satellite in self.satellites.items():
                if cur_satellite_id == satellite_id or satellite_id in processed:
                    continue

                p1 = cur_satellite.pos
                p2 = satellite.pos
                e3 = [(p2[0] - p1[0]), (p2[1] - p1[1]), (p2[2] - p1[2])]
                e3_mod2 = e3[0] ** 2 + e3[1] ** 2 + e3[2] ** 2
                e1 = [
                    (p1[0] - self.earth.model.getX()),
                    (p1[1] - self.earth.model.getY()),
                    (p1[2] - self.earth.model.getZ()),
                ]
                e1_mod2 = e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2

                cos_beta_2 = (e1[0] * e3[0] + e1[1] * e3[1] + e1[2] * e3[2]) ** 2 / (
                    e1_mod2 * e3_mod2
                )

                cos_alpha_2 = self.earth.radius / e1_mod2

                if cos_beta_2 < cos_alpha_2:
                    self.graph.add_edge(cur_satellite_id, satellite_id)

            processed.add(cur_satellite_id)

        if self.sender and self.recipient:
            self.path = self.get_shortest_path()

        self.topology_timer = Timer(self.update_interval, self.update_topology)
        self.topology_timer.start()

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

    def check_path(self):
        if len(self.path) < 3 or not self.sender or not self.recipient:
            self.path = []
            return

        dash_id = self.path[0]
        satellite_id = self.path[1]
        dash = self.dashes[dash_id]
        satellite = self.satellites[satellite_id]
        p1 = dash.pos
        p2 = satellite.pos
        e1 = [
            p1[0] - self.earth.model.getX(),
            p1[1] - self.earth.model.getY(),
            p1[2] - self.earth.model.getZ(),
        ]
        e2 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
        cos2 = (e1[0] * e2[0] + e1[1] * e2[1] + e1[2] * e2[2]) / np.sqrt(
            (e1[0] * e1[0] + e1[1] * e1[1] + e1[2] * e1[2])
            * (e2[0] * e2[0] + e2[1] * e2[1] + e2[2] * e2[2])
        )
        if cos2 <= self.dash_cone_cos2:
            self.path = []
            return

        dash_id = self.path[-1]
        satellite_id = self.path[-2]
        dash = self.dashes[dash_id]
        satellite = self.satellites[satellite_id]
        p1 = dash.pos
        p2 = satellite.pos
        e1 = [
            p1[0] - self.earth.model.getX(),
            p1[1] - self.earth.model.getY(),
            p1[2] - self.earth.model.getZ(),
        ]
        e2 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
        cos2 = (e1[0] * e2[0] + e1[1] * e2[1] + e1[2] * e2[2]) / np.sqrt(
            (e1[0] * e1[0] + e1[1] * e1[1] + e1[2] * e1[2])
            * (e2[0] * e2[0] + e2[1] * e2[1] + e2[2] * e2[2])
        )
        if cos2 <= self.dash_cone_cos2:
            self.path = []
            return

        for i in range(1, len(self.path) - 2):
            cur_satellite_id = self.path[i]
            satellite_id = self.path[i + 1]
            cur_satellite = self.satellites[cur_satellite_id]
            satellite = self.satellites[satellite_id]
            p1 = cur_satellite.pos
            p2 = satellite.pos
            e3 = [(p2[0] - p1[0]), (p2[1] - p1[1]), (p2[2] - p1[2])]
            e3_mod2 = e3[0] ** 2 + e3[1] ** 2 + e3[2] ** 2
            e1 = [
                (p1[0] - self.earth.model.getX()),
                (p1[1] - self.earth.model.getY()),
                (p1[2] - self.earth.model.getZ()),
            ]
            e1_mod2 = e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2

            cos_beta_2 = (e1[0] * e3[0] + e1[1] * e3[1] + e1[2] * e3[2]) ** 2 / (
                e1_mod2 * e3_mod2
            )

            cos_alpha_2 = self.earth.radius / e1_mod2

            if cos_beta_2 >= cos_alpha_2:
                self.path = []
                return

    def _update(self):
        for line in self.lines:
            line.remove_node()

        self.lines = []
        self.check_path()

        if len(self.path) == 0:
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
