#!/usr/bin/env python3.7
import pro6
import queue
import logging
import sys
from time import sleep
import datetime
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
target_host = "aztec.local."
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

    p6_remote = pro6.WebSocket(PASSWORD, '_pro6proremote', remote_endpoint, message_queue)
    p6_stage = pro6.WebSocket(PASSWORD, '_pro6stagedsply', remote_endpoint, message_queue)
    p6_remote.run()
    p6_stage.run()

    while not p6_stage.connected and not p6_remote.connected:
        logging.debug('Waiting for connections...')
        sleep(1)

    # request initial state
    p6_stage.stage_configuration()
    p6_remote.current_presentation()
    p6_remote.current_slide()
    p6_clock = pro6.Clock(message_queue=message_queue)

    pi_lcd.clear()

    while True:
        try:
            if not message_queue.empty():
                incoming_message = message_queue.get_nowait()
                if incoming_message.kind is pro6.Message.Kind.ACTION:
                    message_handler.do(incoming_message)
                elif incoming_message.kind is pro6.Message.Kind.EVENT:
                    if incoming_message.name == 'slide_change':
                        # we need two things from pro6 - one is the index of
                        # the new slide and the presentation if we don't have
                        # it already
                        pi_lcd_send('clear')
                        p6_clock.reset()
                        p6_clock.slide_index = incoming_message['index']
                        if not p6_clock.ready:
                            pi_lcd_send('display_message', 'No slide data')
                    elif incoming_message.name == 'presentation_change':
                        pi_lcd_send('clear')
                        p6_clock.reset()
                        p6_clock.presentation = incoming_message['presentation']
                        if not p6_clock.ready:
                            pi_lcd_send('display_message', 'No slide data')
                    elif incoming_message.name == 'segment_change':
                        if PI_PLATFORM:
                            pi_lcd_send('show_segment', p6_clock.segment_name)
                    elif incoming_message.name == 'video_advance':
                        p6_clock.update_clock(incoming_message['timecode'])
                        if PI_PLATFORM and p6_clock.ready:
                            pi_lcd_send('show_time_remaining', total_time_remaining=p6_clock.video_duration_remaining, segment_time_remaining=p6_clock.segment_time_remaining)
                            pi_lcd_send('show_time_elapsed', time_elapsed=p6_clock.current_video_position)
                            if p6_clock.segment_time_remaining <= datetime.timedelta(seconds=5):
                                pi_led_send('red', p6_clock.segment_time_remaining)
                            elif p6_clock.segment_time_remaining <= datetime.timedelta(seconds=10):
                                pi_led_send('yellow', p6_clock.segment_time_remaining)
                            elif p6_clock.segment_time_remaining <= datetime.timedelta(seconds=30):
                                pi_led_send('green')
                            else:
                                pi_led_send('clear')
                    else:
                        print("Unhandled event: %s" % incoming_message)
                else:
                    print("Unhandled queue object: %s" % incoming_message)

        except KeyboardInterrupt:
            logging.info("shutting down")
            p6_remote.stop()
            p6_stage.stop()

            sys.exit(0)
