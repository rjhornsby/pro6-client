#!/usr/bin/env python3.7
import pro6
import queue
import logging
import sys
from time import sleep
import platform

PI_PLATFORM = False
pi_lcd = None
pi_led = None
if platform.system() == 'Linux':
    PI_PLATFORM = True
    import pi
    pi_lcd = pi.LCD()
    pi_led = pi.LED()

PASSWORD = 'control'
# target_host = "%s.local." % gethostname()
target_host = "warrior.local."
logging.basicConfig(level=logging.INFO)


def pi_lcd_send(method, *args, **kwargs):
    if pi_lcd is None: return

    handler_method = getattr(pi_lcd, method)(*args, **kwargs)
    if callable(handler_method):
        handler_method(method)


def pi_led_send(method, *args, **kwargs):
    if pi_led is None: return

    handler_method = getattr(pi_led, method)(*args, **kwargs)
    if callable(handler_method):
        handler_method(method)

if __name__ == "__main__":

    logging.info('Starting up, detected platform %s' % str(platform.system()))

    message_queue = queue.SimpleQueue()
    message_handler = pro6.Handler(message_queue)

    pi_lcd_send('display_message', "Searching for Pro6", lcd_line=1)

    remote_endpoint = pro6.Discovery("_pro6proremote", target_host).discover()

    pi_lcd_send('clear')
    pi_lcd_send('display_message', "Connecting to", lcd_line=1)
    pi_lcd_send('display_message', remote_endpoint, lcd_line=2)

    p6_stage = pro6.WebSocket(PASSWORD, '_pro6stagedsply', remote_endpoint, message_queue)
    p6_stage.run()

    while not p6_stage.connected:  # and not p6_remote.connected:
        logging.debug('Waiting for connections...')
        sleep(1)

    # request initial state
    p6_stage.stage_configuration()
    p6_clock = pro6.Clock(message_queue=message_queue)

    pi_lcd_send('clear')

    if pi_lcd is not None:
        p6_clock.subscribe(pi_lcd)

    if pi_led is not None:
        p6_clock.subscribe(pi_led)

    while True:
        try:
            if not message_queue.empty():
                incoming_message = message_queue.get_nowait()
                if incoming_message.kind is pro6.Message.Kind.ACTION:
                    message_handler.do(incoming_message)
                elif incoming_message.kind is pro6.Message.Kind.EVENT:
                    if incoming_message.name == 'slide_change':
                        p6_clock.new_slide(incoming_message['segment_markers'])
                    elif incoming_message.name == 'segment_change':
                        pass
                    elif incoming_message.name == 'video_advance':
                        p6_clock.update_clock(incoming_message['timecode'])
                    else:
                        print("Unhandled event: %s" % incoming_message)
                else:
                    print("Unhandled queue object: %s" % incoming_message)

        except KeyboardInterrupt:
            logging.info("shutting down")
            p6_stage.stop()

            sys.exit(0)
