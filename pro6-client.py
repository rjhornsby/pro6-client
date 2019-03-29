#!/usr/bin/env python3.7
import pro6
import queue
import logging
import sys
from time import sleep
import yaml

RTC_DISPLAY_ENABLE = True

PASSWORD = 'control'
# TODO: Make this search for a list of hosts
# TODO: Handle a reset condition - ie ProPresenter goes away

logging.basicConfig(level=logging.getLevelName('INFO'))


def load_config():
    try:
        logging.debug('Reading config')
        with open('config.yml', 'r') as config_file:
            y_config = yaml.safe_load(config_file)
    except IOError as e:
        logging.critical('Unable to load configuration file config.yml: %s', e.strerror)
        sys.exit(1)

    return y_config


if __name__ == "__main__":
    config = load_config()
    logging.basicConfig(level=logging.getLevelName(config['logging_level'].upper()))
    host_list = map(lambda host: host + '.local.', config['host_search'])

    logging.info('Starting up')

    message_queue = queue.SimpleQueue()

    p6_client = pro6.Client(config, message_queue)
    p6_client.lcd.display_message("Searching for Pro6", lcd_line=1)

    remote_endpoint = pro6.Discovery("_pro6stagedsply", host_list).discover()

    p6_client.lcd.clear()
    p6_client.lcd.display_message("Connecting to", lcd_line=1)
    p6_client.lcd.display_message(remote_endpoint, lcd_line=2)

    p6_stage = pro6.WebSocket(PASSWORD, '_pro6stagedsply', remote_endpoint, message_queue)
    p6_stage.subscribe(p6_client)
    p6_stage.run()

    while not p6_stage.connected:
        logging.debug('Waiting for connection...')
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
