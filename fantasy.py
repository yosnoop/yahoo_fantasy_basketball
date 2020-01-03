from dataclasses import dataclass, fields
from yahoo_oauth import OAuth2
from pprint import pprint
import yahoo_fantasy_api as yfa

CATEGORY = {'fg', 'ft', 'threept', 'pts', 'reb', 'ast', 'st', 'blk', 'to'}


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0


@dataclass
class Player():
    player_id: str
    name: str
    position_type: str
    fg: float
    ft: float
    threept: float
    pts: float
    reb: float
    ast: float
    st: float
    blk: float
    to: float

    def __post_init__(self):
        for f in fields(self):
            if f.type == float:
                setattr(self, f.name, to_float(getattr(self, f.name)))


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
        player = Player(*stats.values())
        print(stats['name'])
        self.roster[stats['name']] = player


class League():
    def __init__(self, game):
        league = game.to_league(game.league_ids()[-1])
        self.my_team_key = league.team_key()
        self.teams = [
            Team(league, t['team_key'], league.to_team(t['team_key']).roster())
            for t in league.teams()
        ]
        self.league = league

    def standing(self, category: str):
        stats = {team.key: team.stat(category) for team in self.teams}
        reverse = False if category == 'to' else True
        return sorted(stats.items(), key=lambda kv: kv[1], reverse=reverse)

    def myrank(self):
        ranks = 0
        for cat in CATEGORY:
            for i, stat in enumerate(self.standing(cat)):
                if stat[0] == self.my_team_key:
                    ranks += i
        return ranks / len(CATEGORY)

    def free_agents(self, position):
        return self.league.free_agents(position)


oauth = OAuth2(None, None, from_file='oauth2.json')
gm = yfa.Game(oauth, 'nba')
lg = League(gm)

for position in ['PG', 'SG', 'SF', 'PF', 'C']:
    pprint(lg.free_agents(position))
