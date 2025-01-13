from direct.gui.DirectGui import *


class Menu:
    def __init__(self, parent, n, callback):
        self.n = n

        self.frame = DirectFrame(
            parent=parent,
            pos=(-1.4, 0, 0.7),
            frameSize=(-0.35, 0.35, -0.35, 0.2),
            frameColor=(0.8, 0.8, 0.8, 0.4),
        )

        self.label1 = DirectLabel(
            parent=self.frame,
            text="Select sender:",
            scale=0.05,
            pos=(-0.175, 0, 0.15),
            frameColor=(0.8, 0.8, 0.8, 0.0),
        )

        self.sender = 0
        self.sender_button = DirectOptionMenu(
            parent=self.frame,
            pos=(0.05, 0, 0.15),
            frameSize=(-0.0375, 5.0, -0.1125, 0.75),
            scale=0.05,
            items=[f"Sender {i}" for i in range(1, n + 1)],
            initialitem=self.sender,
            command=self.update_sender,
        )

        self.label2 = DirectLabel(
            parent=self.frame,
            text="Select receiver:",
            scale=0.05,
            pos=(-0.157, 0, 0.08),
            frameColor=(0.8, 0.8, 0.8, 0.0),
        )

        self.receiver = 1
        self.receiver_button = DirectOptionMenu(
            parent=self.frame,
            pos=(0.05, 0, 0.08),
            frameSize=(-0.0375, 5.0, -0.1125, 0.75),
            scale=0.05,
            items=[f"Receiver {i}" for i in range(1, n + 1)],
            initialitem=self.receiver,
            command=self.update_receiver,
        )

        self.label3 = DirectLabel(
            parent=self.frame,
            text="Packages:",
            scale=0.05,
            pos=(-0.225, 0, 0.01),
            frameColor=(0.8, 0.8, 0.8, 0.0),
        )

        self.packages_count = 100
        self.num_packages_line = DirectEntry(
            parent=self.frame,
            pos=(0.05, 0, 0.01),
            frameSize=(-0.0375, 5.6, -0.1125, 0.75),
            scale=0.05,
            initialText=str(self.packages_count),
            command=self.update_packages_count,
            focusInCommand=self.clear_count,
        )

        self.label4 = DirectLabel(
            parent=self.frame,
            text="Correct parameters",
            scale=0.05,
            pos=(-0.0, 0, -0.06),
            frameColor=(0.8, 0.8, 0.8, 0.0),
        )

        # Создаем кнопку
        self.start_button = DirectButton(
            parent=self.frame,
            pos=(-0.0, 0, -0.13),  # Центр фрейма по горизонтали, ниже второго пункта
            scale=0.05,
            text="Transmit",
            command=self.start_transmit,
        )

        self.label5 = DirectLabel(
            parent=self.frame,
            text="",
            scale=0.05,
            pos=(-0.0, 0, -0.2),
            frameColor=(0.8, 0.8, 0.8, 0.0),
        )

        self.callback = callback

    def update_sender(self, value):
        self.sender = int(value.split(" ")[1]) - 1
        if self.sender == self.receiver:
            self.start_button["state"] = DGG.DISABLED
            self.label4["text"] = "Incorrect parameters"
        else:
            self.start_button["state"] = DGG.NORMAL
            self.label4["text"] = "Correct parameters"

    def update_receiver(self, value):
        self.receiver = int(value.split(" ")[1]) - 1
        if self.sender == self.receiver:
            self.start_button["state"] = DGG.DISABLED
            self.label4["text"] = "Incorrect parameters"
        else:
            self.start_button["state"] = DGG.NORMAL
            self.label4["text"] = "Correct parameters"

    def clear_count(self):
        self.num_packages_line.enterText("")

    def update_packages_count(self, value):
        try:
            self.packages_count = int(value)
        except:
            self.packages_count = 100
            self.num_packages_line.enterText(str(self.packages_count))

    def start_transmit(self):
        self.callback(self.sender, self.receiver, self.packages_count)

    def set_progress(self, progress_str):
        self.label5["text"] = progress_str
