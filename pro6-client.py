#!/usr/bin/env python3.7
import pro6
import queue
import logging
import sys
from time import sleep

RTC_DISPLAY_ENABLE = False

PASSWORD = 'control'
# TODO: Make this search for a list of hosts
# TODO: Handle a reset condition - ie ProPresenter goes away
pro6_host_search = ["foo.local", "warrior.local."]
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":

    logging.info('Starting up')

    message_queue = queue.SimpleQueue()

    p6_client = pro6.Client(message_queue)
    p6_client.lcd.display_message("Searching for Pro6", lcd_line=1)

    remote_endpoint = pro6.Discovery("_pro6stagedsply", pro6_host_search).discover()

    p6_client.lcd.clear()
    p6_client.lcd.display_message("Connecting to", lcd_line=1)
    p6_client.lcd.display_message(remote_endpoint, lcd_line=2)

    p6_stage = pro6.WebSocket(PASSWORD, '_pro6stagedsply', remote_endpoint, message_queue)
    p6_stage.subscribe(p6_client)
    p6_stage.run()

    while not p6_stage.connected:
        logging.debug('Waiting for connections...')
        sleep(1)

    p6_client.lcd.clear()
    p6_client.lcd.rtc_run()


    while True:
        try:
            sleep(1)

        except KeyboardInterrupt:
            logging.info("shutting down")
            p6_stage.stop()
            p6_client.stop()

            sys.exit(0)
