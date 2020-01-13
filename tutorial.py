import logging

from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader

logging.basicConfig(level=logging.INFO)

datafetch = DataFetcher()

datafetch.get_player_clean_gamelog("Bruce Brown")

[player for player in datafetch.nba_players_list if player[0]=="J"]

#datafetch.get_player_performance("Nikola Jokic",60)

matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input.xlsx")

game = matchupreader.process_game(out)

game["Home"]

home = matchupreader.get_already_passed_games(out["Home"])

home


players_played = home[
    home["GAME_PLAYED"]==1
    ]["PLAYER_NAME"]

players_played

team_sheet = out["Home"].merge(
    right=home.loc[home["PLAYER_NAME"].isin(players_played),
    ["PLAYER_NAME","MIN","FP","FPPM"]],
    on=["PLAYER_NAME"],
    how="left"
)



performances = matchupreader.get_already_passed_games(out["Away"])

performances