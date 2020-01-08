## Test nba api to download stats from Python

from nba_api.stats.endpoints import playercareerstats

import pandas as pd


career = playercareerstats.PlayerCareerStats(player_id="203076")

career.season_rankings_post_season

from nba_api.stats.static import teams

nba_teams = teams.get_teams()

nba_teams[:3]

from nba_api.stats.static import players


nba_players = players.get_players()

nba_players[:3]


kareem = playercareerstats.PlayerCareerStats(player_id="76003")

kareem.get_data_frames()[0]

### get all games from a team (current season, Atlanta 1610612737)
from nba_api.stats.endpoints import teamgamelog

gamelog = teamgamelog.TeamGameLog(team_id="1610612737")

gamelog.get_data_frames()[0]

## get play by play from desired game (0021900543 ATL vs DEN)
from nba_api.stats.endpoints import playbyplay

gamepbp = playbyplay.PlayByPlay(game_id="0021900543")

gamepbp.get_data_frames()[0].sort_values("EVENTNUM")

## get traditional box score from the same game
from nba_api.stats.endpoints import boxscoretraditionalv2

boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id="0021900543")

boxscore.get_data_frames()[0]

## based on teamgamelog and box score, we could calculate the FPPM for each player
## but how to link games to players? have to go through team?

from nba_api.stats.endpoints import playergamelog

gamelog = playergamelog.PlayerGameLog(player_id="203999", season="2018-19")

gamelog.get_data_frames()[0]

# does it include DNPs?
### seems it does not

### One(?) does have to create a class that returns relevant FPs for a given player
## and game number (Nikola Vucevic, game 35)
