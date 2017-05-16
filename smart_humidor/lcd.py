#!/usr/bin/env python

import argparse
import datetime
import logging
import sys
import time

import smart_humidor.util.display as display
from smart_humidor.config import HumidorConfig
from smart_humidor.util.graphite import GraphiteClient
from smart_humidor.util.icons import icons

GRAPHITE_WEB_ADDR = 'http://127.0.0.1:8000/render'
SENSORS_CONFIG = '/etc/opt/smart-humidor/sensors.yaml'


class HumidorLCD:
    LINE_INDENT = 2
    LOOP_INTERVAL = 1

    def __init__(self):
        self.config = HumidorConfig()
        render_url = '/'.join([self.config.graphite.url.rstrip('/'), 'render'])
        self.graphite = GraphiteClient(url=render_url)

        display.init()
        display.disclear(0)
        display.init_text()
        self.init_icons()
        self.draw_icons()

    @staticmethod
    def init_icons():
        for k, v in icons.items():
            display.defikon(k, v)

    @staticmethod
    def draw_icons():
        for k in icons:
            display.printiko(k, 0, k)

    @staticmethod
    def parse_metrics(metrics):
        d = {}
        for metric in metrics:
            for datapoint in reversed(metric['datapoints']):
                if datapoint[0] is not None:
                    d[metric['target']] = datapoint[0]
        return d

    @staticmethod
    def get_metrics():
        target = 'humidor.*.*.trim'
        since = '3min'

        graphite = GraphiteClient(GRAPHITE_WEB_ADDR)
        metrics = graphite.get_metric(target, since)
        return metrics

    def print_line(self, text, level):
        display.velky_napis(text, self.LINE_INDENT, level)

    def print_metrics(self, metrics):
        d = {}
        for k, value in metrics.items():
            index, metric, sensor = k.split('.')[:3]
            pin = sensor[-2:]  # this should work as long as RPi GPIO are under 100, but naming should be revised
            sensor = self.config.get_sensor(pin)

            if sensor.level not in d.keys():
                d[sensor.level] = {}
            d[sensor.level][metric] = value

        for k, v in d.items():
            line = " {}C {}%  ".format(v['temperature'], v['humidity'])
            self.print_line(line, k)

    def print_time(self):
        n = datetime.datetime.now().time().strftime(' %H:%M:%S')
        self.print_line(n, self.config.get_sensor(0).level)

    def loop(self):
        while True:
            self.print_time()
            metrics = self.get_metrics()
            if metrics:
                logging.debug('Collected metrics: {}'.format(metrics))
                parsed = self.parse_metrics(metrics)
                self.print_metrics(parsed)
        
            time.sleep(self.LOOP_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description='Smart Humidor LCD')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
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

    lcd = HumidorLCD()
    try:
        lcd.loop()
    except KeyboardInterrupt:
        logging.info('Interrupted!')

if __name__ == '__main__':
    main()
