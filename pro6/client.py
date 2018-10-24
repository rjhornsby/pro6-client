# import threading
import logging
from lib.observer import Subscriber
from lib.observer import Notifier
import pro6
import pi


class Client(Subscriber, Notifier):
    def __init__(self, msg_queue):
        self._msg_queue = msg_queue
        self._message_handler = pro6.Handler(msg_queue)
        self._p6_clock = pro6.Clock()

        self.lcd = pi.LCD()
        self.led = pi.LED()

        self.event = None

        self._p6_clock.subscribe(self.lcd)
        self.subscribe(self._p6_clock)

        # if RTC_DISPLAY_ENABLE: self.lcd.rtc_run()

    def stop(self):
        self.lcd.rtc_stop()

    def notify(self, obj, param, value):
        if param == 'message_pending':
            self.process_messages()

    def process_messages(self):
        while not self._msg_queue.empty():
            incoming_message = self._msg_queue.get_nowait()
            if incoming_message.kind is pro6.Message.Kind.ACTION:
                self._message_handler.do(incoming_message)
            elif incoming_message.kind is pro6.Message.Kind.EVENT:
                self.event = incoming_message
            else:
                print("Unhandled queue object: %s" % incoming_message)
