#!/usr/local/bin/python3
import pro6
import queue
import logging
import sys
from time import sleep
from socket import gethostname
import platform

PASSWORD = 'control'
target_host = "%s.local." % gethostname()
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":

    logging.info('Starting up, detected platform %s' % str(platform.system()))

    message_queue = queue.SimpleQueue()

    message_handler = pro6.Handler(message_queue)

    remote_endpoint = pro6.Discovery("_pro6proremote", target_host).discover()

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

    while True:
        try:
            if not message_queue.empty():
                incoming_message = message_queue.get_nowait()
                if incoming_message.kind is pro6.Message.Kind.ACTION:
                    message_handler.do(incoming_message)
                elif incoming_message.kind is pro6.Message.Kind.EVENT:
                    if incoming_message.name == 'slide_change':
                        # we need two pro6 - one is the index of the new slide
                        # and the presentation if we don't have it already
                        p6_clock.reset()
                        p6_clock.slide_index = incoming_message['index']
                    elif incoming_message.name == 'presentation_change':
                        p6_clock.reset()
                        p6_clock.presentation = incoming_message['presentation']
                    elif incoming_message.name == 'video_advance':
                        p6_clock.update_clock(incoming_message['timecode'])
                         #print(p6_clock.segment_time_remaining)
                    else:
                        print("Unhandled event: %s" % incoming_message)
                else:
                    print("Unhandled queue object: %s" % incoming_message)

        except KeyboardInterrupt:
            logging.info("shutting down")
            p6_remote.stop()
            p6_stage.stop()

            sys.exit(0)
