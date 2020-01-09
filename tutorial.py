from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader

datafetch = DataFetcher()

datafetch.get_player_clean_gamelog("Nikola Jokic")

matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input.xlsx")

