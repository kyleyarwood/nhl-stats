'''Module for getting teams and team info'''
import logging
from typing import Any
import requests

from .constants import API_URL, API_VERSION, DEFAULT_TIMEOUT
from .player import Player


LOG = logging.getLogger('team_logger')

def get_teams(only_active: bool = False) -> list['Team']:
    '''Gets all NHL teams'''
    url = f'{API_URL}/{API_VERSION}/teams'
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json()['teams']
    except requests.exceptions.HTTPError as error:
        LOG.exception('Received an HTTPError when trying to get all teams: %s', error)
        raise error
    except KeyError as error:
        LOG.exception('Ran into a problem with API output: %s', error)
        raise error
    teams = []
    for team_info in data:
        if only_active and not team_info.get('active', False):
            continue
        team = Team(team_id=team_info['id'])
        team.load_basic_info(team_info)
        teams.append(team)
    return teams

class Team:
    '''Represents an NHL team'''
    ATTRIBUTE_TO_API_ATTRIBUTE = {
        'name': 'name',
        'abbreviation': 'abbreviation',
        'team_name': 'teamName',
        'location_name': 'locationName',
        'first_year_of_play': 'firstYearOfPlay',
        'active': 'active'
    }

    def __init__(self, team_id: int):
        self.team_id = team_id
        self._loaded_basic_info = False

    def load_basic_info(self, basic_info: dict) -> None:
        '''
        Loads basic info given to the team class
        Parameters:
            basic_info: contains information in Team.ATTRIBUTE_TO_API_ATTRIBUTE
        '''
        for attribute, api_attribute in Team.ATTRIBUTE_TO_API_ATTRIBUTE.items():
            setattr(self, attribute, basic_info.get(api_attribute))
        self._loaded_basic_info = True

    def _get_basic_info(self) -> None:
        if self._loaded_basic_info:
            return
        url = f'{API_URL}/{API_VERSION}/teams/{self.team_id}'

        try:
            response = requests.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()['teams'][0]
        except requests.exceptions.HTTPError as error:
            LOG.exception(
                'Received an HTTPError when trying to get team %i: %s', self.team_id, error
            )
            raise error
        except KeyError as error:
            LOG.exception('Ran into a problem with API output: %s', error)
            raise error
        self.load_basic_info(data)

    def get_roster(self, season: str = '') -> list['Player']:
        '''
        Gets team roster for specified season

        Parameters:
            season: season that you want the roster for, e.g. '20162017'
        Returns:
            a list of Player objects representing the players on the roster
        '''
        params = {'expand': 'team.roster'}
        if season:
            params['season'] = season
        url = f'{API_URL}/{API_VERSION}/teams/{self.team_id}'

        try:
            response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()['teams'][0]['roster']['roster']
        except requests.exceptions.HTTPError as error:
            LOG.exception(
                'Received an HTTPError when trying to get roster for team %i: %s', 
                self.team_id,
                error,
            )
            raise error
        except KeyError as error:
            LOG.exception('Ran into a problem with API output: %s', error)
            raise error

        return [Player(player_id=player_info['person']['id']) for player_info in data]

    def __getattr__(self, __name) -> Any:
        if __name in Team.ATTRIBUTE_TO_API_ATTRIBUTE:
            self._get_basic_info()
        else:
            pass
        return self.__getattribute__(__name)
        