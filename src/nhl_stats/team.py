import logging
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

    def load_basic_info(self, basic_info: dict) -> None:
        '''
        Loads basic info given to the team class
        Parameters:
            basic_info: contains information in Team.ATTRIBUTE_TO_API_ATTRIBUTE
        '''
        for attribute, api_attribute in Team.ATTRIBUTE_TO_API_ATTRIBUTE.items():
            setattr(self, attribute, basic_info.get(api_attribute))

    def get_roster(self, season: str = '') -> list['Player']:
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
        