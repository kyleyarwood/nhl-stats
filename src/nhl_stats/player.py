'''Class for player info and stats'''
import logging
from typing import Any
import requests

from .constants import API_URL, API_VERSION

class Player:
    '''Represents an NHL player'''

    ATTRIBUTE_TO_API_ATTRIBUTE = {
        'name': 'fullName',
        'number': 'primaryNumber',
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
        'roster_status': 'rosterStatus',
    }

    VALID_STATS = {
        'yearByYear',
        'homeAndAway',
        'winLoss',
        'byMonth',
        'byDayOfWeek',
        'vsDivision',
        'vsConference',
        'vsTeam',
        'gameLog',
        'regularSeasonStatRankings',
        'goalsByGameSituation',
        'onPaceRegularSeason',
    }

    def __init__(self, player_id: int):
        self.player_id = player_id
        self._loaded_basic_info = False
        self._log = logging.getLogger('player_log')

    def get_stats(self, stats: str, season: str = ''):
        '''
        Return stats for a season, defaults to current season

        Parameters:
            stats: the type of stats, has to belong to Player.VALID_STATS
            season: which season you want stats for, e.g. '20162017'
        Returns:
            TBD
        '''
        if stats not in Player.VALID_STATS:
            raise ValueError(f'{stats} is not a valid stat type')
        if stats == 'yearByYear' and season:
            raise ValueError('Season can\'t be specified when stats is yearByYear')

        url = f'{API_URL}/{API_VERSION}/people/{self.player_id}/stats'
        params = {'stats': stats}

        if season:
            params['season'] = season

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()['stats']
        except requests.exceptions.HTTPError as error:
            self._log.exception(
                'Received an HTTPError when trying to get player\'s stats %i: %s', 
                self.player_id,
                error,
            )
            raise error
        except KeyError as error:
            self._log.exception('Ran into a problem with API output: %s', error)
            raise error

        return data

    def _get_basic_info(self) -> None:
        if self._loaded_basic_info:
            return
        url = f'{API_URL}/{API_VERSION}/people/{self.player_id}'

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()['people'][0]
        except requests.exceptions.HTTPError as error:
            self._log.exception(
                'Received an HTTPError when trying to get player %i: %s', self.player_id, error
            )
            raise error
        except KeyError as error:
            self._log.exception('Ran into a problem with API output: %s', error)
            raise error

        for attribute, api_attribute in Player.ATTRIBUTE_TO_API_ATTRIBUTE.items():
            setattr(self, attribute, data.get(api_attribute, None))
        self._loaded_basic_info = True

    def __getattr__(self, __name: str) -> Any:
        if __name in Player.ATTRIBUTE_TO_API_ATTRIBUTE:
            self._get_basic_info()
        else:
            pass
        return self.__getattribute__(__name)
    