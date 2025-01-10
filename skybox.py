from panda3d.core import DepthTestAttrib, RenderAttrib, Shader


class Skybox:
    def __init__(self, loader):
        try:
            # Загрузка текстуры окружения
            self.cubemap = loader.loadCubeMap("models/skybox/face_#.png")

            # Загрузка куба
            self.model = loader.loadModel("models/skybox/skybox.egg")

            # Настройка отображения
            self.model.setShader(
                Shader.load(
                    Shader.SLGLSL,
                    "shaders/skybox_vert.glsl",
                    "shaders/skybox_frag.glsl",
                )
            )
            self.model.setShaderInput("TexSkybox", self.cubemap)
            self.model.setAttrib(DepthTestAttrib.make(RenderAttrib.MLessEqual))
            self.model.setLightOff()

            print("Skybox loaded successfully")
        except Exception as e:
            print(f"Error loading skybox: {e}")
