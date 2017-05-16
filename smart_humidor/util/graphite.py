import requests
import logging


class GraphiteClient:
    def __init__(self, url='http://localhost:8000/render'):
        self.url = url

    def _get(self, params):
        r = requests.get(self.url, params=params)
        if r.status_code == requests.codes.ok:
            logging.debug('Raw response {}'.format(r.text))
            return r.json()
        else:
            logging.error('Request failed with reponse code {}'.format(r.status_code))
            return None

    def get_metric(self, target, since):
        params = {
            'target': target,
            'from': '-{}'.format(since),
            'format': 'json'
        }
        return self._get(params=params)

