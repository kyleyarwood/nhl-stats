'''Class for player info and stats'''
import logging
from typing import Any
import requests

from .constants import API_URL, API_VERSION

class Player:
    '''Represents an NHL player'''

    ATTRIBUTE_TO_API_ATTRIBUTE = {
        'name': 'fullName',
        'number': 'playerNumber',
        'birth_date': 'birthDate',
        'birth_city': 'birthCity',
        'birth_state_province': 'birthStateProvince',
        'birth_country': 'birthCountry',
        'nationality': 'nationality',
        'height': 'height',
        'weight': 'weight',
        'active': 'active',
        'rookie': 'rookie',
        'shoots_catches': 'shootsCatches',
        'roster_status': 'rosterStatus'
    }

    def __init__(self, player_id: int):
        self.player_id = player_id
        self._loaded_basic_info = False
        self._log = logging.getLogger('player_log')
        for attribute in Player.ATTRIBUTE_TO_API_ATTRIBUTE:
            setattr(self, attribute, None)

    def _get_basic_info(self) -> None:
        if self._loaded_basic_info:
            return
        url = f'{API_URL}/{API_VERSION}/player/{self.player_id}'
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            self._log.exception(
                'Received an HTTPError when trying to get player %i: %s', self.player_id, error
            )
            raise error
        data = response.json()
        for attribute, api_attribute in Player.ATTRIBUTE_TO_API_ATTRIBUTE: # pylint: disable=unbalanced-dict-unpacking
            setattr(self, attribute, data.get(api_attribute, None))
        self._loaded_basic_info = True

    def __getattribute__(self, __name: str) -> Any:
        if __name not in Player.ATTRIBUTE_TO_API_ATTRIBUTE:
            return None
        self._get_basic_info()
        return getattr(self, __name)
    