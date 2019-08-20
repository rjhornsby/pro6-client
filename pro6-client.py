#!/usr/bin/env python3.7
import pro6
import queue
import logging
import sys
from time import sleep
import yaml
from osc4py3.as_eventloop import *

RTC_DISPLAY_ENABLE = True
# TODO: Handle a reset condition - ie ProPresenter goes away


def load_config():
    try:
        with open('config.yml', 'r') as config_file:
            y_config = yaml.safe_load(config_file)
    except IOError as e:
        logging.critical('Unable to load configuration file config.yml: %s', e.strerror)
        sys.exit(1)

    return y_config


if __name__ == "__main__":
    config = load_config()

    fmt = "%(levelname)-8.8s [%(name)s:%(module)s:%(funcName)s] %(message)s"
    logging.basicConfig(format=fmt, level=logging.getLevelName(config['logging_level'].upper()))

    logging.info('Log level %s', logging.getLevelName(logging.getLogger().level))
    logging.info('Starting up')

    message_queue = queue.SimpleQueue()

    p6_client = pro6.Director(config, message_queue)
    p6_client.run()

    while True:
        try:
            sleep(2)
        except KeyboardInterrupt:
            logging.info("shutting down")
            p6_client.stop()
            sys.exit(0)
