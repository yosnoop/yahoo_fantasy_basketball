from yahoo_oauth import OAuth2
from pprint import pprint
import yahoo_fantasy_api as yfa
from time import sleep

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
    maximum_roster = 13

    def __init__(self, league, key, roster):
        self.league = league
        self.key = key
        self.roster = {}
        self.cache = {}
        for p in roster:
            self.add(p)

    def stat(self, category):
        return sum(getattr(p_, category) for p_ in self.roster.values())

    def drop(self, player_id):
        del self.roster[player_id]

    def add(self, player):
        if len(self.roster) >= Team.maximum_roster:
            raise ValueError('Cannot add. Roster is full.')
        player_id = player['player_id']
        cached = self.cache.get(player_id)
        if cached:
            self.roster[player_id] = cached
        else:
            stats = self.league.player_stats(player_id, 'lastmonth')[0]
            stats.update({'eligible_positions': player['eligible_positions']})
            newplayer = Player(**stats)
            self.roster[player_id] = newplayer
            self.cache[player_id] = newplayer
            print(self.roster[player_id].name)


class League():
    positions = ['PG', 'SG', 'SF', 'PF', 'C']
    non_tradable = [4901, 5007]

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
                if stat[0] == self.my_team.key:
                    result[cat] = i
        return result

    def find_prospects(self, list_, position=None):
        result = []
        current_avgrank = sum(self.myrank().values()) / len(CATEGORY)
        for candidate in list_:
            sleep(1)
            for player_id, player in self.my_team.roster.copy().items():
                if candidate['status'] != '':
                    continue
                if player_id in League.non_tradable:
                    continue
                if position is None:
                    common_positions = \
                        list(
                            set(player.eligible_positions).intersection(
                                candidate['eligible_positions']
                            )
                        )
                    if len(common_positions) >= len(['Util']):
                        continue
                if position is not None and \
                        position not in player.eligible_positions:
                    continue
                self.my_team.drop(player_id)
                self.my_team.add(candidate)
                avgrank = sum(self.myrank().values()) / len(CATEGORY)
                delta = current_avgrank - avgrank
                if delta > 0:
                    print("Ranks: " + str(self.myrank()))
                    print("Average rank: {:.3f}".format(avgrank))
                    result.append(
                        (candidate, delta, player.player_id)
                    )
                self.my_team.drop(candidate['player_id'])
                self.my_team.roster[player_id] = player
        return result

    def recommend(self):
        recommendation = []
        recommendation.extend(self.find_prospects(self.league.waivers()))
        for position in League.positions:
            recommendation.extend(
                self.find_prospects(
                    self.league.free_agents(position),
                    position
                )
            )
        return recommendation

    def add_and_drop(self):
        recommendation = self.recommend()
        if len(recommendation) == 0:
            return
        top = sorted(recommendation, key=lambda x: x[1], reverse=True)[0]
        pprint(top)
        if top[1] < 0.7:
            print(f"The delta ({top[1]}) is too small to make the change")
            return
        self.league.to_team(self.my_team.key).add_and_drop_players(
            top[0]['player_id'],
            top[2]
        )


oauth = OAuth2(None, None, from_file='oauth2.json')
gm = yfa.Game(oauth, 'nba')
lg = League(gm)
lg.add_and_drop()
