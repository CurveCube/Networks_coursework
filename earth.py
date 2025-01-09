import time

class Earth:
    def __init__(self, loader, time_factor=100):
        self.radius = 6.371
        self.t0 = time.time()
        self.rotation_step = -360 / (24 * 3600) * time_factor

        try:
            # Загрузка модели GLTF
            self.model = loader.loadModel("models/earth/scene.gltf")

            # Настройка масштаба модели
            pt1, pt2 = self.model.getTightBounds()
            size = (pt2.getX() - pt1.getX()) / 2
            self.model.setScale(self.radius / size)

            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")

    def update(self, task):
        # Вращение модели
        delta_t = self.t0 - time.time()
        angle = delta_t * self.rotation_step
        self.model.setH(angle)

        return task.again
