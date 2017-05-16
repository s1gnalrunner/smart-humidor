#!/usr/bin/env python

import argparse
import logging
import socket
import sys
import time

import Adafruit_DHT
from smart_humidor.config import HumidorConfig


class HumidorSensor:
    def __init__(self, pin):
        self.pin = pin
        self.sensor = Adafruit_DHT.DHT22
        self.config = HumidorConfig()
        self.carbon = None
        self.connect()

    def connect(self):
        if self.carbon:
            self.carbon.close()

        self.carbon = socket.socket()

        try:
            self.carbon.connect((self.config.carbon.host, self.config.carbon.port))
        except ConnectionRefusedError:
            logging.error('Failed connecting to carbon. Is carbon running?')

    def send(self, data):
        try:
            self.carbon.send(bytes((data + '\n').encode()))
        except BrokenPipeError:
            logging.error('Failed pushing data to carbon. Is carbon running?')
            self.connect()

    def read(self):
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        raw = {
            'humidity': humidity,
            'temperature': temperature,
        }

        if humidity is not None and temperature is not None:
            for k, v in raw.items():
                data = self.format_data(k, v)
                logging.debug(data)
                self.send(data)

                trimmed_data = self.format_data(k, v, trim=True)
                self.send(trimmed_data)
        else:
            logging.error('Failed to get reading.')

    def format_data(self, metric_type, value, trim=False):
        metric_name = ['humidor', metric_type, 'sensor{}'.format(self.pin)]
        if trim:
            metric_name.append('trim')
            value = self.trim(metric_type, value)
        metric_name = '.'.join(metric_name)
        return '{0} {1:0.1f} {2}'.format(metric_name, value, time.time())

    def trim(self, metric_type, value):
        try:
            return value + self.config.get_sensor(self.pin).trim[metric_type]
        except KeyError:
            logging.debug('Trim offset not found for {}:{}'.format(self.pin, metric_type))
            return value

    def loop(self):
        while True:
            self.read()


def main():
    parser = argparse.ArgumentParser(description='Smart Humidor Metrics collector')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('pin', metavar='PIN', type=int, help='GPIO pin number')

    args = parser.parse_args()

    root = logging.getLogger()
    if args.verbose:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    sensor = HumidorSensor(args.pin)

    try:
        sensor.loop()
    except KeyboardInterrupt:
        logging.info('Interrupted!')

if __name__ == '__main__':
    main()
