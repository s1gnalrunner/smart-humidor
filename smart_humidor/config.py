import yaml
from abc import ABC


class HumidorConfig:
    CONFIG = '/etc/opt/smart-humidor/config.yaml'

    def __init__(self):
        raw = self.load_config(self.CONFIG)
        self.sensors = list(self.configure_sensors(raw['sensors']))
        self.carbon = CarbonConfig(**raw['carbon'])
        self.graphite = GraphiteConfig(**raw['graphite'])

    @staticmethod
    def load_config(file):
        with open(file, 'r') as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def configure_sensors(raw):
        for sensor in raw:
            yield SensorConfig(**sensor)

    def get_sensor(self, pin):
        for sensor in self.sensors:
            if sensor.pin == int(pin):
                return sensor
        raise UnknownSensorError('Could not find config entry for pin {}'.format(pin))


class BaseConfig(ABC):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class SensorConfig(BaseConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CarbonConfig(BaseConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class GraphiteConfig(BaseConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class UnknownSensorError(Exception):
    pass
