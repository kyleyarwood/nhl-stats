'''Module for getting teams and team info'''
from dataclasses import dataclass
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
    _ATTRIBUTE_TO_API_ATTRIBUTE = {
        'name': 'name',
        'abbreviation': 'abbreviation',
        'team_name': 'teamName',
        'location_name': 'locationName',
        'first_year_of_play': 'firstYearOfPlay',
        'active': 'active'
    }

    STATS_API_ATTRIBUTE_TO_STAT_ATTRIBUTE = {
        'gamesPlayed': 'games_played',
        'wins': 'wins',
        'losses': 'losses',
        'ot': 'ot',
        'pts': 'pts',
        'ptPctg': 'pt_pctg',
        'goalsPerGame': 'goals_per_game',
        'goalsAgainstPerGame': 'goals_against_per_game',
        'evGGARatio': 'ev_gga_ratio',
        'powerPlayPercentage': 'powerplay_percentage',
        'powerPlayGoals': 'powerplay_goals',
        'powerPlayGoalsAgainst': 'powerplay_goals_against',
        'powerPlayOpportunities': 'powerplay_opportunities',
        'penaltyKillPercentage': 'penalty_kill_percentage',
        'shotsPerGame': 'shots_per_game',
        'shotsAllowed': 'shots_allowed_per_game',
        'winScoreFirst': 'win_score_first',
        'winOppScoreFirst': 'win_opp_score_first',
        'winLeadFirstPer': 'win_lead_first_per',
        'winLeadSecondPer': 'win_lead_second_per',
        'winOutshootOpp': 'win_outshoot_opp',
        'winOutshotByOpp': 'win_outshot_by_opp',
        'faceOffsTaken': 'faceoffs_taken',
        'faceOffsWon': 'faceoffs_won',
        'faceOffsLost': 'faceoffs_lost',
        'faceOffWinPercentage': 'faceoff_win_percentage',
        'shootingPctg': 'shooting_pctg',
        'savePctg': 'save_pctg',
    }

    def __init__(self, team_id: int):
        self.team_id = team_id
        self._loaded_basic_info = False

    def load_basic_info(self, basic_info: dict) -> None:
        '''
        Loads basic info given to the team class
        Parameters:
            basic_info: contains information in Team._ATTRIBUTE_TO_API_ATTRIBUTE
        '''
        for attribute, api_attribute in Team._ATTRIBUTE_TO_API_ATTRIBUTE.items():
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
                - will default to current season
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

    def get_team_stats(self, season: str = '') -> 'TeamStats':
        '''
        Gets team stats for specified season

        Parameters:
            season: season that you want the stats for, e.g. '20162017'
                - will default to current season
        Returns:
            a TeamStats object representing the team's stats for the season
        '''
        params = {'expand': 'team.stats'}
        if season:
            params['season'] = season
        url = f'{API_URL}/{API_VERSION}/teams/{self.team_id}'

        try:
            response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()['teams'][0]['teamStats'][0]['splits'][0]['stat']
        except requests.exceptions.HTTPError as error:
            LOG.exception(
                'Received an HTTPError when trying to get stats for team %i: %s', 
                self.team_id,
                error,
            )
            raise error
        except KeyError as error:
            LOG.exception('Ran into a problem with API output: %s', error)
            raise error
        transformed_data = {
            Team.STATS_API_ATTRIBUTE_TO_STAT_ATTRIBUTE[api_attribute]: value
            for api_attribute, value in data.items()
        }
        return TeamStats(**transformed_data)

    def __getattr__(self, __name) -> Any:
        if __name in Team._ATTRIBUTE_TO_API_ATTRIBUTE:
            self._get_basic_info()
        else:
            pass
        return self.__getattribute__(__name)

@dataclass
class TeamStats: #pylint: disable=too-many-instance-attributes
    '''Stats for a team in a given season'''
    games_played: int
    wins: int
    losses: int
    ot: int #pylint: disable=invalid-name
    pts: int
    pt_pctg: str
    goals_per_game: float
    goals_against_per_game: float
    ev_gga_ratio: float
    powerplay_percentage: str
    powerplay_goals: int
    powerplay_goals_against: int
    powerplay_opportunities: int
    penalty_kill_percentage: str
    shots_per_game: float
    shots_allowed_per_game: float
    win_score_first: float
    win_opp_score_first: float
    win_lead_first_per: float
    win_lead_second_per: float
    win_outshoot_opp: float
    win_outshot_by_opp: float
    faceoffs_taken: int
    faceoffs_won: int
    faceoffs_lost: int
    faceoff_win_percentage: str
    shooting_pctg: float
    save_pctg: float
