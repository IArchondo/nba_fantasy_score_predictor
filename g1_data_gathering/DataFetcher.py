import pandas as pd
import numpy as np
import math

from nba_api.stats.static import teams
from nba_api.stats.static import players
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import playergamelog

import logging

logger = logging.getLogger("DataFetcher")

logging.basicConfig(level=logging.INFO)

### One(?) does have to create a class that returns relevant FPs for a given player
## and game number (Nikola Vucevic, game 35)

class DataFetcher:
    def __init__(self):
        self.nba_players = players.get_players()
        self.players_id_dict = {
            self.nba_players[i]["full_name"]: self.nba_players[i]["id"]
            for i in range(len(self.nba_players))
        }
        self.nba_players_list = [self.nba_players[i]["full_name"]
            for i in range(len(self.nba_players))]

    def __fetch_player_id(self, player_name):
        """Hidden method to fetch a given player's NBA API Id

        Args:
            player_name (str): [description]
        """
        try:
            player_id = self.players_id_dict[player_name]
        except KeyError:
            raise Exception("Player not found in database")
        return player_id

    def __get_player_raw_gamelogs(self, player_name):
        """Hidden method that returns a player's gamelog given a player's name
        
        Args:
            player_name (str): Player's complete name (ex: Nikola Vucevic)
        
        Returns:
            gamelog_df: pd.DataFrame
        """
        player_id = self.__fetch_player_id(player_name)
        logger.info("Gathering gamelogs for player "+str(player_name)+"...")
        gamelog = playergamelog.PlayerGameLog(player_id=player_id)

        gamelog_df = gamelog.get_data_frames()[0]

        gamelog_df.loc[:, "GAME_DATE"] = pd.to_datetime(gamelog_df["GAME_DATE"])

        gamelog_df.loc[:, "Team"] = gamelog_df["MATCHUP"].astype(str).str[0:3]

        gamelog_df.loc[:, "Team_ID"] = gamelog_df["Team"].apply(
            lambda x: teams.find_team_by_abbreviation(x)["id"]
        )
        # round minutes up (sports ws seems to do that)
        #TODO minute comes already rounded up. Try to solve this, although
        # it is probably very complicated
        gamelog_df.loc[:,"MIN"] = gamelog_df["MIN"].apply(
            lambda x:math.ceil(x)
        )

        gamelog_df = gamelog_df.drop(["Team", "PLUS_MINUS", "VIDEO_AVAILABLE"], axis=1)

        return gamelog_df

    def __get_team_gamelog(self, team_id):
        """Hidden method to get a given team's gamelog
        
        Args:
            team_id (int): Team ID
        
        Returns:
            pd.DataFrame: Team's gamelog and game number
        """
        team_gamelog = teamgamelog.TeamGameLog(team_id=team_id)
        logger.info("Getting teams gamelogs")
        team_gamelog = team_gamelog.get_data_frames()[0]

        team_gamelog["GAME_DATE"] = pd.to_datetime(team_gamelog["GAME_DATE"])

        team_gamelog = team_gamelog.sort_values("GAME_DATE")

        team_gamelog = team_gamelog.reset_index()

        team_gamelog = team_gamelog.drop(["index"], axis=1)

        team_gamelog.loc[:, "GAME_NUMBER"] = team_gamelog.index + 1

        cols_to_keep = [
            "Team_ID",
            "Game_ID",
            "GAME_DATE",
            "MATCHUP",
            "GAME_NUMBER",
            "WL",
        ]

        team_gamelog = team_gamelog[cols_to_keep]

        return team_gamelog

    def __assign_gamenumber_to_player_gamelog(self, player_gamelog):
        """Assign the gamenumber to a player gamelog, also fill in missing games
        
        Args:
            player_gamelog (pd.DataFrame): player's gamelog
        
        Returns:
            pd.DataFrame: Player's gamelog with game number
        """
        teams_played_for = player_gamelog["Team_ID"].unique()
        teams_gamelogs = pd.concat(
            [self.__get_team_gamelog(team) for team in teams_played_for]
        )
        player_gamelog = player_gamelog.merge(
            right=teams_gamelogs,
            how="outer",
            on=["Team_ID", "Game_ID", "GAME_DATE", "MATCHUP", "WL"],
        )

        player_gamelog = player_gamelog.sort_values(["GAME_NUMBER", "GAME_DATE"])

        player_gamelog = player_gamelog.loc[
            player_gamelog.notnull()
            .sum(1)
            .groupby(player_gamelog.GAME_NUMBER[::-1])
            .idxmax()
        ]

        # fix missing values
        player_id = [
            id for id in player_gamelog["Player_ID"].unique() if not np.isnan(id)
        ][0]
        player_gamelog.loc[:, "Player_ID"] = player_id

        # season_id = [id for id in player_gamelog["SEASON_ID"].unique() if not np.isnan(id)][0]
        # TODO: make it season sensitive
        player_gamelog.loc[:, "SEASON_ID"] = "22019"

        player_gamelog = player_gamelog.fillna(0)

        return player_gamelog

    def __calculate_fantasy_points(self, player_gamelog):
        """Calculate fantasy points for all given games
        
        Args:
            player_gamelog (pd.DataFrame): Player gamelog
        
        Returns:
            pd.DataFrame: Player gamelog with calculated fantasy points
        """

        player_gamelog.loc[:, "WIN_BONUS"] = (player_gamelog["WL"] == "W").astype(int)

        player_gamelog.loc[:, "FP"] = (
            player_gamelog["PTS"]
            + 2 * player_gamelog["AST"]
            + 2 * player_gamelog["STL"]
            + 2 * player_gamelog["BLK"]
            + 1 * player_gamelog["DREB"]
            + player_gamelog["WIN_BONUS"]
            + 1.5 * player_gamelog["OREB"]
            - 2 * player_gamelog["TOV"]
            - 0.5 * (player_gamelog["FGA"] - player_gamelog["FGM"])
            - 0.5 * (player_gamelog["FTA"] - player_gamelog["FTM"])
        )

        player_gamelog.loc[player_gamelog["MIN"] == 0, "FP"] = 0

        player_gamelog.loc[:, "FPPM"] = round(
            player_gamelog["FP"] / player_gamelog["MIN"], 2
        )
        player_gamelog.loc[player_gamelog["MIN"] == 0, "FPPM"] = 0

        return player_gamelog

    def get_player_clean_gamelog(self, player_name):
        """Fetch complete player gamelog, assign game numbers and calculate
            fantasy points
        
        Args:
            player_name (str): Player name
        
        Returns:
            pd.DataFrame: Clean processed player gamelog
        """
        raw_player_gamelog = self.__get_player_raw_gamelogs(player_name)
        raw_player_gamelog = self.__assign_gamenumber_to_player_gamelog(
            raw_player_gamelog
        )
        player_gamelog = self.__calculate_fantasy_points(raw_player_gamelog)

        return player_gamelog

    def get_player_performance(self, player_name, game_number):
        """Get a player's performance in a certain game

        Args:
            player_name (str): Player name
            game_number (int): Game number

        Returns:
            pd.DataFrame: Dataframe with all needed stats
        """
        player_gamelog = self.get_player_clean_gamelog(player_name)

        if game_number in player_gamelog["GAME_NUMBER"]:
            performance = player_gamelog.loc[
                player_gamelog["GAME_NUMBER"] == game_number, :
            ]
            performance.loc[:, "PLAYER_NAME"] = player_name
            performance.loc[:,"GAME_PLAYED"] = 1

            performance = performance[
                [
                    "PLAYER_NAME",
                    "GAME_NUMBER",
                    "GAME_PLAYED",
                    "GAME_DATE",
                    "MATCHUP",
                    "WL",
                    "MIN",
                    "FGM",
                    "FGA",
                    "FTM",
                    "FTA",
                    "OREB",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "TOV",
                    "PTS",
                    "FP",
                    "FPPM",
                ]
            ]

        else:
            performance = player_gamelog.loc[
                player_gamelog["GAME_NUMBER"] == 1, :
            ]

            performance.loc[:, "PLAYER_NAME"] = player_name
            performance.loc[:,"GAME_PLAYED"] = 0
            performance.loc[:,"GAME_NUMBER"] = game_number

            performance = performance[
                [
                    "PLAYER_NAME",
                    "GAME_NUMBER",
                    "GAME_PLAYED",
                    "GAME_DATE",
                    "MATCHUP",
                    "WL",
                    "MIN",
                    "FGM",
                    "FGA",
                    "FTM",
                    "FTA",
                    "OREB",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "TOV",
                    "PTS",
                    "FP",
                    "FPPM",
                ]
            ]

            performance.loc[:,
            [
                "GAME_DATE",
                    "MATCHUP",
                    "WL",
                    "MIN",
                    "FGM",
                    "FGA",
                    "FTM",
                    "FTA",
                    "OREB",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "TOV",
                    "PTS",
                    "FP",
                    "FPPM"
            ]] = np.nan

        return performance

