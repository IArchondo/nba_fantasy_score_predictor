import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger("MatchupReader")

## class has to read a given matchup, and format the outcome so it can be read
## by the following step
# TODO: in the 2.0 version, this should be able to read from basketball.sports.ws directly

class MatchupReader():
    def __init__(self):
        logging.info("MatchupReader initiated")
        self.valid_positions = ["G","F","C","GF","FG","FC","CF"]
        self.input_columns = ["Player","Game","Position","Team"]

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

    def read_given_excel(self,path_string):
        input_excel = pd.read_excel(Path(path_string))
        self.__check_input_ok(input_excel)
        logging.info("Input excel fulfills all required criteria")
        
        # create dict with home and away teams
        matchup_dict = {}
        matchup_dict["Home"] = input_excel[input_excel["Team"]=="Home"]
        matchup_dict["Away"] = input_excel[input_excel["Team"]=="Away"]

        for key in matchup_dict.keys():
            matchup_dict[key] = matchup_dict[key].drop(["Team"],axis=1)
        
        logging.info("Input excel reformatted")

        return matchup_dict




