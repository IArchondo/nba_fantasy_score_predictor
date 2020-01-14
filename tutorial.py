import logging

from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader
from g4_matchup_calculator.MatchupCalculator import MatchupCalculator

logging.basicConfig(level=logging.INFO)

datafetch = DataFetcher()

player = datafetch.get_player_clean_gamelog("Christian Wood")

#datafetch.get_player_performance("Nikola Jokic",60)

matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input.xlsx")

matchupcalculator = MatchupCalculator(out)

match = matchupcalculator.process_game(matchupcalculator.input_matchup)

