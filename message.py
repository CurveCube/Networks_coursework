import enum

import numpy as np


class MessageStatus(enum.Enum):
    OK = enum.auto()
    LOST = enum.auto()


class Message:
    number = -1
    real_number = -1
    data = ""
    status = MessageStatus.OK

    def __init__(self):
        pass

    def copy(self):
        msg = Message()
        msg.number = self.number
        msg.data = self.data
        msg.status = self.status
        return msg


class MsgQueue:
    def __init__(self, loss_probability=0.3):
        self.msg_queue = []
        self.loss_probability = loss_probability
        pass

    def has_msg(self):
        if len(self.msg_queue) <= 0:
            return False
        else:
            return True

    def get_message(self):
        if self.has_msg():
            result = self.msg_queue[0]
            self.msg_queue.pop(0)
            return result

    def send_message(self, msg):
        tmp_msg = self.emulating_channel_problems(msg)
        self.msg_queue.append(tmp_msg)

    def emulating_channel_problems(self, msg):
        val = np.random.rand()
        if val <= self.loss_probability:
            msg.status = MessageStatus.LOST

        return msg
