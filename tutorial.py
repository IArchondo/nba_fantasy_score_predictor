import logging

from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader
from g3_performance_modeler.PerformanceModeler import PerformanceModeler
from g4_matchup_calculator.MatchupCalculator import MatchupCalculator

logging.basicConfig(level=logging.INFO)

# datafetch = DataFetcher()

# player = datafetch.get_player_clean_gamelog("Fred VanVleet")

# performance_modeler = PerformanceModeler()

# performance_forecasts = performance_modeler.determine_forecast(player)

# out = datafetch.get_player_performance("Nikola Jokic",60)


matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input_2.xlsx")

matchupcalculator = MatchupCalculator(out)

output = matchupcalculator.generate_forecasts(out,1000)

logging.info("Hola"+str(100)+"% porciento")


