import enum
import time

from message import Message, MessageStatus


class SRP_sender:
    class WndMsgStatus(enum.Enum):
        BUSY = enum.auto()
        NEED_REPEAT = enum.auto()
        CAN_BE_USED = enum.auto()

    class WndNode:
        def __init__(self, number):
            self.status = SRP_sender.WndMsgStatus.NEED_REPEAT
            self.time = 0
            self.number = number
            pass

    def __init__(
        self,
        answer_msg_queue,
        send_msg_queue,
        posted_msgs,
        window_size,
        max_number,
        timeout,
    ):
        self.answer_msg_queue = answer_msg_queue
        self.send_msg_queue = send_msg_queue
        self.posted_msgs = posted_msgs
        self.window_size = window_size
        self.max_number = max_number
        self.timeout = timeout
        self.wnd_nodes = [SRP_sender.WndNode(i) for i in range(window_size)]
        self.ans_count = 0

    def send(self):
        if self.ans_count < self.max_number:
            if self.answer_msg_queue.has_msg():
                ans = self.answer_msg_queue.get_message()
                self.ans_count += 1
                self.wnd_nodes[ans.number].status = SRP_sender.WndMsgStatus.CAN_BE_USED

            # долго нет ответа с последнего подтверждения
            curr_time = time.time()
            for i in range(self.window_size):
                if self.wnd_nodes[i].number >= self.max_number:
                    continue

                send_time = self.wnd_nodes[i].time
                if curr_time - send_time > self.timeout:
                    # произошёл сбой, нужно повторить отправку этого сообщения
                    self.wnd_nodes[i].status = SRP_sender.WndMsgStatus.NEED_REPEAT

            # отправляем новые или повторяем, если необходимо
            for i in range(self.window_size):
                if self.wnd_nodes[i].number >= self.max_number:
                    continue

                if self.wnd_nodes[i].status == SRP_sender.WndMsgStatus.BUSY:
                    continue

                elif self.wnd_nodes[i].status == SRP_sender.WndMsgStatus.NEED_REPEAT:
                    self.wnd_nodes[i].status = SRP_sender.WndMsgStatus.BUSY
                    self.wnd_nodes[i].time = time.time()

                    msg = Message()
                    msg.number = i
                    msg.real_number = self.wnd_nodes[i].number
                    self.send_msg_queue.send_message(msg)
                    self.posted_msgs.append(f"{msg.real_number}({msg.number})")

                elif self.wnd_nodes[i].status == SRP_sender.WndMsgStatus.CAN_BE_USED:
                    self.wnd_nodes[i].status = SRP_sender.WndMsgStatus.BUSY
                    self.wnd_nodes[i].time = time.time()
                    self.wnd_nodes[i].number = (
                        self.wnd_nodes[i].number + self.window_size
                    )

                    if self.wnd_nodes[i].number >= self.max_number:
                        continue

                    msg = Message()
                    msg.number = i
                    msg.real_number = self.wnd_nodes[i].number
                    self.send_msg_queue.send_message(msg)
                    self.posted_msgs.append(f"{msg.real_number}({msg.number})")

    def is_finished(self):
        return self.ans_count == self.max_number


class SRP_receiver:
    def __init__(self, answer_msg_queue, send_msg_queue, received_msgs):
        self.answer_msg_queue = answer_msg_queue
        self.send_msg_queue = send_msg_queue
        self.received_msgs = received_msgs

    def receive(self):
        while self.send_msg_queue.has_msg():
            curr_msg = self.send_msg_queue.get_message()

            if curr_msg.status == MessageStatus.LOST:
                return

            ans = Message()
            ans.number = curr_msg.number
            self.answer_msg_queue.send_message(ans)
            self.received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")
