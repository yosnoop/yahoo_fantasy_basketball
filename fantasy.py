from yahoo_oauth import OAuth2
from pprint import pprint
import yahoo_fantasy_api as yfa

CATEGORY = {'FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO'}


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0


class Player():
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            value = to_float(v) if k in CATEGORY else v
            setattr(self, k, value)


class Team():
    def __init__(self, league, key, roster):
        self.league = league
        self.key = key
        self.roster = {}
        for p in roster:
            self.add(p)

    def stat(self, name):
        return sum(getattr(player, name) for player in self.roster.values())

    def drop(self, name):
        del self.roster[name]

    def add(self, player):
        player_id = player['player_id']
        stats = self.league.player_stats(player_id, 'lastmonth')[0]
        player = Player(**stats)
        print(stats['name'])
        self.roster[stats['name']] = player


class League():
    def __init__(self, game):
        league = game.to_league(game.league_ids()[-1])
        self.teams = []
        self.my_team = None
        for team in league.teams():
            team_key = team['team_key']
            t = Team(league, team_key, league.to_team(team_key).roster())
            if self.my_team is None and team_key == league.team_key():
                self.my_team = t
            self.teams.append(t)
        self.league = league

    def standing(self, category: str):
        stats = {team.key: team.stat(category) for team in self.teams}
        reverse = False if category == 'TO' else True
        return sorted(stats.items(), key=lambda kv: kv[1], reverse=reverse)

    def myrank(self):
        result = {}
        for cat in CATEGORY:
            for i, stat in enumerate(self.standing(cat)):
                if stat[0] == self.my_team['team_key']:
                    result[cat] = i
        return result

    def free_agents(self, position):
        return self.league.free_agents(position)


oauth = OAuth2(None, None, from_file='oauth2.json')
gm = yfa.Game(oauth, 'nba')
lg = League(gm)

for position in ['PG', 'SG', 'SF', 'PF', 'C']:
    pprint(lg.free_agents(position))
