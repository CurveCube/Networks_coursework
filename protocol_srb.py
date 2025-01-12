import enum
import time


from message import Message, MessageStatus

class SRP_sender:
    def __init__ (self, answer_msg_queue, send_msg_queue, posted_msgs):
        self.answer_msg_queue = answer_msg_queue
        self.send_msg_queue = send_msg_queue
        self.posted_msgs = posted_msgs

    def __call__(self, window_size, max_number, timeout):
        class WndMsgStatus(enum.Enum):
            BUSY = enum.auto()
            NEED_REPEAT = enum.auto()
            CAN_BE_USED = enum.auto()

        class WndNode:
            def __init__(self, number):
                self.status = WndMsgStatus.NEED_REPEAT
                self.time = 0
                self.number = number
                pass

            def __str__(self):
                return f"( {self.number}, {self.status}, {self.time})"

        wnd_nodes = [WndNode(i) for i in range(window_size)]

        ans_count = 0

        while ans_count < max_number:

            res_str = "["
            for i in range(window_size):
                res_str += wnd_nodes[i].__str__()
            res_str += "]"

            if self.answer_msg_queue.has_msg():
                ans = self.answer_msg_queue.get_message()
                ans_count += 1
                wnd_nodes[ans.number].status = WndMsgStatus.CAN_BE_USED

            # долго нет ответа с последнего подтверждения
            curr_time = time.time()
            for i in range(window_size):
                if wnd_nodes[i].number > max_number:
                    continue

                send_time = wnd_nodes[i].time
                if curr_time - send_time > timeout:
                    # произошёл сбой, нужно повторить отправку этого сообщения
                    wnd_nodes[i].status = WndMsgStatus.NEED_REPEAT

            # отправляем новые или повторяем, если необходимо
            for i in range(window_size):
                if wnd_nodes[i].number > max_number:
                    continue

                if wnd_nodes[i].status == WndMsgStatus.BUSY:
                    continue

                elif wnd_nodes[i].status == WndMsgStatus.NEED_REPEAT:
                    wnd_nodes[i].status = WndMsgStatus.BUSY
                    wnd_nodes[i].time = time.time()

                    msg = Message()
                    msg.number = i
                    msg.real_number = wnd_nodes[i].number
                    self.send_msg_queue.send_message(msg)
                    self.posted_msgs.append(f"{msg.real_number}({msg.number})")

                elif wnd_nodes[i].status == WndMsgStatus.CAN_BE_USED:
                    wnd_nodes[i].status = WndMsgStatus.BUSY
                    wnd_nodes[i].time = time.time()
                    wnd_nodes[i].number = wnd_nodes[i].number + window_size

                    if wnd_nodes[i].number > max_number:
                        continue

                    msg = Message()
                    msg.number = i
                    msg.real_number = wnd_nodes[i].number
                    self.send_msg_queue.send_message(msg)
                    self.posted_msgs.append(f"{msg.real_number}({msg.number})")

        msg = Message()
        msg.data = "STOP"
        self.send_msg_queue.send_message(msg)


class SRP_receiver:
    def __init__ (self, answer_msg_queue, send_msg_queue, received_msgs):
        self.answer_msg_queue = answer_msg_queue
        self.send_msg_queue = send_msg_queue
        self.received_msgs = received_msgs

    def __call__(self, window_size):
        while True:
            if self.send_msg_queue.has_msg():
                curr_msg = self.send_msg_queue.get_message()

                if curr_msg.data == "STOP":
                    break

                if curr_msg.status == MessageStatus.LOST:
                    continue

                ans = Message()
                ans.number = curr_msg.number
                self.answer_msg_queue.send_message(ans)
                self.received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")