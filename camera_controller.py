import math


class CameraController:
    def __init__(
        self,
        camera,
        taskMgr,
        mouseWatcherNode,
        focus=(0, 0, 0),
        rotation_angle=0,
        rotation_angle_vertical=0,
        camera_radius=40,
    ):
        self.camera = camera
        self.taskMgr = taskMgr
        self.mouseWatcherNode = mouseWatcherNode

        # Инициализация направления взгляда
        self.focus = focus

        # Инициализация углов вращения
        self.rotation_angle = rotation_angle
        self.rotation_angle_vertical = rotation_angle_vertical

        # Инициализация радиуса орбиты камеры
        self.camera_radius = camera_radius

        # Инициализация начальных позиций мыши
        self.mouse_start_x = None
        self.mouse_start_y = None

        self.update_camera_pos()

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

        self.update_camera_pos()

    def zoom_out(self):
        # Уменьшение радиуса орбиты камеры
        self.camera_radius *= 1.1

        self.update_camera_pos()

    def update_camera(self, task):
        # Обновление углов вращения на основе движения мыши
        if (
            self.mouseWatcherNode.hasMouse()
            and self.mouse_start_x is not None
            and self.mouse_start_y is not None
        ):
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()

            # Вычисление разницы позиций мыши
            delta_x = x - self.mouse_start_x
            delta_y = y - self.mouse_start_y

            # Обновление углов вращения
            self.rotation_angle += delta_x * 100
            self.rotation_angle_vertical += delta_y * 100

            # Ограничение вертикального угла вращения
            self.rotation_angle_vertical = max(
                min(self.rotation_angle_vertical, 80), -80
            )

            # Обновление начальной позиции мыши
            self.mouse_start_x = x
            self.mouse_start_y = y

            self.update_camera_pos()

        return task.cont

    def update_camera_pos(self):
        # Вычисление новой позиции камеры
        angleRadians = math.radians(self.rotation_angle)
        angleRadiansVertical = math.radians(self.rotation_angle_vertical)

        self.camera.setPos(
            self.camera_radius
            * math.sin(angleRadians)
            * math.cos(angleRadiansVertical),
            -self.camera_radius
            * math.cos(angleRadians)
            * math.cos(angleRadiansVertical),
            self.camera_radius * math.sin(angleRadiansVertical),
        )
        self.camera.lookAt(*self.focus)  # Направьте камеру на модель
