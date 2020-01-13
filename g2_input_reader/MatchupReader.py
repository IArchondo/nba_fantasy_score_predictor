import pandas as pd
from pathlib import Path
import logging

from g1_data_gathering.DataFetcher import DataFetcher

logger = logging.getLogger("MatchupReader")

## class has to read a given matchup, and format the outcome so it can be read
## by the following step
# TODO: in the 2.0 version, this should be able to read from basketball.sports.ws directly

#TODO keep player order!

class MatchupReader():
    def __init__(self):
        logging.info("MatchupReader initiated")
        self.valid_positions = ["G","F","C","GF","FG","FC","CF"]
        self.input_columns = ["Player","Game","Position","Team"]
        
        self.datafetcher = DataFetcher()

    def __check_input_ok(self,input_table):
        assert all(col in self.input_columns
            for col in input_table.columns),(
            "Required columns are missing"
        )
        assert len(input_table)==24, "Player list is missing players"
        assert len(input_table[input_table["Team"]=="Away"])==12,(
            "Away team has to have 12 players"
            )
        assert len(input_table[input_table["Team"]=="Home"])==12,(
            "Away team has to have 12 players"
            )
        assert len(input_table["Game"].unique())==1, (
            "All players have to play the same game"
            )

        available_positions = input_table["Position"].unique()

        assert all(position in self.valid_positions 
            for position in available_positions), (
                "Some positions are wrong"
                )

    def __check_players_exist(self,input_table):
        """Check if the players in a team sheet all exist in the NBA database
        
        Args:
            input_table (pd.DataFrame): Team sheet
        
        Returns:
            boolean: True if all players exist, False otherwise
        """        
        players_exist = [player for player in input_table["Player"] 
            if player in self.datafetcher.nba_players_list]

        players_dont_exist = [player for player in input_table["Player"] 
            if player not in self.datafetcher.nba_players_list]

        if len(players_exist)!=len(input_table["Player"]):
            logging.error("The following players do not exist: "+str(players_dont_exist))
            return_value = False
        else:
            logging.debug("All players exist")
            return_value = True

        return return_value


    def __fix_player_names(self,team_playersheet):
        """Fix potential problems with player names being imported
        
        Args:
            team_playersheet (pd.DataFrame): Table with team players
        
        Returns:
            pd.DataFrame: Player teamsheet with fixed names
        """        
        
        # replace Jr for Jr.
        team_playersheet["Player"] = team_playersheet["Player"].str.replace("Jr$","Jr.")
        #TODO make the following more all encompassing
        team_playersheet["Player"] = team_playersheet["Player"].str.replace("Bruce Brown Jr.","Bruce Brown")
        team_playersheet["Player"] = team_playersheet["Player"].str.replace("Ellie","Elie")
        team_playersheet["Player"] = team_playersheet["Player"].str.replace("Reddick","Redick")

        return team_playersheet


    def read_given_excel(self,path_string):
        """Read a given excel with team sheets
        
        Args:
            path_string (str): Path to the desired excel file
        
        Returns:
            dict: Dictionary with home and away team pandas dataframes
        """        
        input_excel = pd.read_excel(Path(path_string))
        self.__check_input_ok(input_excel)
        logging.info("Input excel fulfills all required criteria")
        
        # create dict with home and away teams
        matchup_dict = {}
        matchup_dict["Home"] = input_excel[input_excel["Team"]=="Home"]
        matchup_dict["Away"] = input_excel[input_excel["Team"]=="Away"]

        # apply a series of team specific adjustments
        for key in matchup_dict.keys():
            # remove unnecesary columns
            matchup_dict[key] = matchup_dict[key].drop(["Team"],axis=1)
            # add player order as key column
            matchup_dict[key] = matchup_dict[key].reset_index(drop=True)
            matchup_dict[key].loc[:,"Order"] = matchup_dict[key].index+1
            # fix possible errors with names
            matchup_dict[key] = self.__fix_player_names(matchup_dict[key])
        
        logging.info("Input excel reformatted")

        return matchup_dict

    def get_already_passed_games(self,team_sheet):
        """Get all performances from games already played for
            a given team
        
        Args:
            team_sheet (pd.DataFrame): Team Sheet
        
        Returns:
            pd.DataFrame: DataFrame with all performances
        """        
        if self.__check_players_exist(team_sheet):
            logger.info("Gathering already existing performances...")            
            game_number = team_sheet["Game"][0]
            performance_list = [
                self.datafetcher.get_player_performance(
                    player_name=player,game_number=game_number
            )
            for player in team_sheet["Player"]]

            performance_df = pd.concat(performance_list)
            
            return performance_df

    def __process_team_performances(self,team_sheet):
        """Process a team
        
        Args:
            team_sheet (pd.DataFrame): Team sheet
        
        Returns:
            pd.DataFrame: Pandas dataframe with performances
        """        
        performance_table = self.get_already_passed_games(team_sheet)
        performance_table = performance_table.rename(
            columns={'PLAYER_NAME':'Player'}
            )
        players_played = performance_table[
            performance_table["GAME_PLAYED"]==1
            ]["Player"]
        team_sheet = team_sheet.merge(
            right=performance_table.loc[performance_table["Player"].isin(players_played),
            ["Player","MIN","FP","FPPM"]],
            on=["Player"],
            how="left"
        )

        return team_sheet

    def __calculate_fp(self,team_sheet):
        #add required columns for calculation
        team_sheet[]

    def process_game(self,game_dict):
        for key in game_dict.keys():
            game_dict[key] = self.__process_team_performances(
                game_dict[key]
            )

        return game_dict


