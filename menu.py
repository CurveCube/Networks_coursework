from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *

class Menu:
    def __init__(self, parent, n, callback):
        self.frame = DirectFrame(
            parent=parent,
            pos=(1.5, 0, 0.7),
            frameSize=(-0.2, 0.07, -0.2, 0.2),
            frameColor=(0.8, 0.8, 0.8, 0.2),
        )

        self.sender_button = DirectOptionMenu(
            parent=self.frame,
            pos=(-0.18, 0, 0.1),
            scale=0.05,
            items=[f"Sender {i}" for i in range(1, n + 1)],
            initialitem=0,
            command=self.update_sender,
        )
        self.sender = 0

        self.reciver_button = DirectOptionMenu(
            parent=self.frame,
            pos=(-0.18, 0, 0),
            scale=0.05,
            items=[f"Reciver {i}" for i in range(1, n + 1)],
            initialitem=0,
            command=self.update_reciver
        )
        self.reciver = 1

        # Создаем кнопку
        self.start_button = DirectButton(
            parent=self.frame,
            pos=(-0.065, 0, -0.1),  # Центр фрейма по горизонтали, ниже второго пункта
            scale=0.05,
            text="Transmit",
            command=self.start_transmit
        )

        self.callback = callback



    def update_sender(self, value):
        self.sender = int(value.split(' ')[1])

    def update_reciver(self, value):
        self.reciver = int(value.split(' ')[1])

    def start_transmit(self):
        self.callback(self.sender, self.reciver, 100)