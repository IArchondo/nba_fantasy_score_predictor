import logging

from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader
from g4_matchup_calculator.MatchupCalculator import MatchupCalculator

logging.basicConfig(level=logging.INFO)

datafetch = DataFetcher()

player = datafetch.get_player_clean_gamelog("Christian Wood")

player

# datafetch.get_player_performance("Nikola Jokic",60)

matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input.xlsx")

matchupcalculator = MatchupCalculator(out)

match = matchupcalculator.process_game(matchupcalculator.input_matchup)


## mock transformation from list to probabilities

# probable FPPMs
import numpy as np

possible_fppm = np.arange(0, 3.1, 0.1)
possible_fppm = [round(value, 2) for value in possible_fppm]

from g1_data_gathering.DataFetcher import DataFetcher
from collections import Counter

datafetch = DataFetcher()
player = datafetch.get_player_clean_gamelog("Giannis Antetokounmpo")

fppms = player[player["MIN"] > 0]["FPPM"]

# replace all negative values with 0
fppms = [0 if value < 0 else value for value in fppms]
fppms = [3 if value > 3 else value for value in fppms]

# round to nearest 0.1
fppms = [round(value * 10) / 10 for value in fppms]

game_count = len(fppms)

# count ocurrences
occ_counter = Counter(fppms)

# insert occurrences into all posible occurrences
general_occ = {}
for pos in possible_fppm:
    if round(pos, 1) in occ_counter.keys():
        value = occ_counter[pos]
    else:
        value = 0
    general_occ[round(pos, 1)] = value

probabilities = [general_occ[key] / game_count for key in general_occ.keys()]

rng = np.random.default_rng()

simulation = rng.multinomial(1, probabilities, size=100)

outcomes = [
    possible_fppm[np.where(simulation[key] == True)[0][0]].sum()
    for key in range(len(simulation))
]

outcomes.sort()

Counter(outcomes)
