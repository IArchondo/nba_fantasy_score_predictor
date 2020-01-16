import pandas as pd
import numpy as np
from collections import Counter
import statistics as stat
import logging

logger = logging.getLogger("PerformanceModeler")

class PerformanceModeler():
    def __init__(self,bin_size=0.1):
        self.possible_fppm = np.arange(0,3.1,bin_size)
        self.possible_fppm = [round(value, 2) for value in self.possible_fppm]
        self.bin_size = bin_size
    
    def __preprocess_player_gamelog_for_fppm(self,player_gamelog):
        """Preprocess player gamelog in order to generate fppm prediction
                - Select only games where player has played
                - Cut outliers
                - Round to neares 0.1
        
        Args:
            player_gamelog (pd.DataFrame): complete player gamelog
        
        Returns:
            list: List with all valid fppms
        """
        logger.debug("Preprocessing player gamelogs...")        
        fppms = player_gamelog[player_gamelog["MIN"]>0]["FPPM"]

        if len(fppms)>0:

            # replace all negative values with 0
            fppms = [0 if value < 0 else value for value in fppms]
            fppms = [3 if value > 3 else value for value in fppms]

            # round to nearest 0.1
            fppms = [round(value * self.bin_size*100) / (self.bin_size *100)
                for value in fppms]

        else:
            logger.error("Player has not played any game")
            raise Exception("Player has not played any game")

        return fppms

    def __calculate_probabilities(self,fppms):
        """Given a list of fppms, calculate their probabilities
        
        Args:
            fppms (list): list with all the player's fppms
        
        Returns:
            list: list with the probabilities for each possible fppm
        """        
        logger.debug("Calculating probabilities...")
        game_count = len(fppms)

        # count number of observations
        occ_counter = Counter(fppms)

        # insert number of observations into all posible occurrences
        general_occ = {}
        for pos in self.possible_fppm:
            if round(pos, 1) in occ_counter.keys():
                value = occ_counter[pos]
            else:
                value = 0
            general_occ[round(pos, 1)] = value

        # calculate probabilities given number of observations
        probabilities = [general_occ[key] / game_count for key in general_occ.keys()]

        return probabilities

    def __run_simulations(self,probabilities,number_of_simulations=100):
        """ Run simulations given a set of probabilities
        
        Args:
            probabilities (list): List of probabilities for each possible fppm
            number_of_simulations (int, optional): Number of desired simulations.
                 Defaults to 100.
        
        Returns:
            np.ndarray: possible_fppm x number_of_simulations array with all 
                simulated outcomes
        """
        if round(sum(probabilities),4)==1:        
            logger.debug("Running simulations for the given player")
            rng = np.random.default_rng()

            simulation = rng.multinomial(1, probabilities, size=100)

            outcomes = [
                self.possible_fppm[np.where(simulation[key] == True)[0][0]].sum()
                for key in range(len(simulation))
            ]

            return outcomes

        else:
            logger.error("Probabilities do not add up to 1")
            raise Exception("Probabilities do not add up to 1")

    def determine_fppm_forecast(self,player_gamelog,number_of_simulations=100):
        """Given a player gamelog, determine minutes played forecast
        
        Args:
           player_gamelog (pd.DataFrame): complete player gamelog
           number_of_simulations (int, optional): Number of desired simulations.
                Defaults to 100.
        
        Returns:
            outcomes: list of simulated outcomes<
        """
        #TODO: give option to do a continuous porbability simulation instead
        #   of discrete        
        fppms = self.__preprocess_player_gamelog_for_fppm(player_gamelog)
        probabilities = self.__calculate_probabilities(fppms)
        outcomes = self.__run_simulations(probabilities,number_of_simulations)

        return outcomes

    
    def determine_minute_forecast(self,player_gamelog):
        """ Given a player gamelog, determine minutes played forecast
        
        Args:
            player_gamelog (pd.DataFrame): complete player gamelog
        
        Returns:
            float: minute forecast
        """
        logger.debug("Calculating player minutes played forecast")        
        ## process player minutes to determine minute forecast
        if all([val==0 for val in player_gamelog["MIN"][-5:]]):
            minute_forecast = 0
        else:
            played_games_min = player_gamelog[player_gamelog["MIN"]>0]["MIN"]
            minute_forecast = round(stat.median(played_games_min[-5:]))

        return minute_forecast

    def determine_forecast(self,player_gamelog,number_of_simulations=100):
        """Run both models to get fppm and minute forecast
        
        Args:
            player_gamelog (pd.DataFrame): complete player gamelog
            number_of_simulations (int, optional): Number of desired simulations.
                Defaults to 100.
        
        Returns:
            dict: Dict with both forecasts
        """        
        logger.info("Determining forecast for given player...")

        fppm_forecast = self.determine_fppm_forecast(player_gamelog,number_of_simulations)
        minute_forecast = self.determine_minute_forecast(player_gamelog)

        output_dict = {"fppm_forecast":fppm_forecast,
            "minute_forecast":minute_forecast}

        logger.info("Done")

        return output_dict




