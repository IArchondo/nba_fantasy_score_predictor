import logging
import pandas as pd

from g1_data_gathering.DataFetcher import DataFetcher

logger = logging.getLogger("MatchupCalculator")

class MatchupCalculator():
    def __init__(self,input_matchup):
        self.positions = ["G","F","C"]

        self.input_matchup = input_matchup
        
        self.datafetcher = DataFetcher()

    def assign_already_played_games(self,team_sheet):
        #TODO pasar al matchup calculator
        """Get all performances from games already played for
            a given team
        
        Args:
            team_sheet (pd.DataFrame): Team Sheet
        
        Returns:
            pd.DataFrame: DataFrame with all performances
        """        
        
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
        performance_table = self.assign_already_played_games(team_sheet)
        performance_table = performance_table.rename(
            columns={'PLAYER_NAME':'Player'}
            )
        players_played = performance_table[
            performance_table["GAME_PLAYED"]==1
            ]["Player"]
        team_sheet = team_sheet.merge(
            right=performance_table.loc[performance_table["Player"].isin(players_played),
            # ["Player","MIN","FP","FPPM"]],
            :],
            on=["Player"],
            how="left"
        )

        return team_sheet

    def __round_fp(self,input_number):
        """Round off float to neares 0.5
        
        Args:
            input_number (float): input number
        
        Returns:
            float: rounded number
        """        
        rounded_number = round(input_number*2)/2

        return rounded_number

    def __calculate_fp(self,team_sheet,no_of_extra_times=0):
        #add required columns for calculation
        team_sheet = team_sheet.loc[:,["Player","Game","Position","Order","Sec_order","MIN","FP","FPPM"]]
        new_columns = [['IM_'+pos,'UM_'+pos,'RM_'+pos] for pos in self.positions]
        new_columns = [item for sublist in new_columns for item in sublist]

        team_sheet = pd.concat([team_sheet,
            pd.DataFrame(columns=new_columns)],sort=False)

        ## fill out new columns
        team_sheet.loc[:,['IM_G','RM_G']] = 96 + no_of_extra_times*10
        team_sheet.loc[:,['IM_F','RM_F']] = 96 + no_of_extra_times*10
        team_sheet.loc[:,['IM_C','RM_C']] = 48 + no_of_extra_times*5

        team_sheet.loc[:,['UM_G','UM_F','UM_C']] = 0


        ## duplicate double position players
        for i in range(len(team_sheet)):
            if len(team_sheet.loc[i,'Position'])>1:
                team_sheet.loc[len(team_sheet)+1,:] = team_sheet.loc[i,:]
                #split positions
                initial_position = team_sheet.loc[i,'Position'][0]
                secondary_position = team_sheet.loc[i,'Position'][1]
                team_sheet.loc[i,'Position'] = initial_position
                team_sheet.loc[len(team_sheet),'Position'] = secondary_position
                # assign hierarchy
                team_sheet.loc[i,'Sec_order'] = 1
                team_sheet.loc[len(team_sheet),'Sec_order'] = 2


        #reorder to maintain general hierarchy
        team_sheet = team_sheet.sort_values(['Order','Sec_order'])
        team_sheet = team_sheet.reset_index(drop=True)

        for i in range(len(team_sheet)):
            if i>0: 
                for pos in ['G','F','C']:
                    team_sheet.loc[i,'IM_'+str(pos)] = team_sheet.loc[i-1,'RM_'+str(pos)] 
            used_position = team_sheet.loc[i,'Position'][0]
            if team_sheet.loc[i,'Sec_order']==2:
                team_sheet.loc[i,'MIN'] = team_sheet.loc[i,'MIN']-team_sheet.loc[i-1,
                [col for col in team_sheet.columns if 'UM' in col]].sum()
            if team_sheet.loc[i,'MIN']<=team_sheet.loc[i,'IM_'+str(used_position)]:
                team_sheet.loc[i,'UM_'+str(used_position)] = team_sheet.loc[i,'MIN']
                
            else:
                team_sheet.loc[i,'UM_'+str(used_position)] = (
                    team_sheet.loc[i,'IM_'+str(used_position)])
                team_sheet.loc[i,'RM_'+str(used_position)] = 0

            for pos in self.positions:
                    team_sheet.loc[i,'RM_'+str(pos)] = (
                        team_sheet.loc[i,'IM_'+str(pos)]-
                        team_sheet.loc[i,'UM_'+str(pos)])

        team_sheet.loc[:,'UM'] = team_sheet.loc[:,
            [col for col in team_sheet.columns if 'UM' in col]].sum(axis=1)

        team_sheet.loc[:,'FPU'] = team_sheet['UM']*team_sheet['FPPM']

        team_sheet.loc[:,'FPU'] = team_sheet.loc[:,'FPU'].apply(lambda x:self.__round_fp(x))

        return team_sheet

    def __determine_winner(self,game_dict):
        """Determine winner of an already filled game_dict
        
        Args:
            game_dict (dict): Dict with filled game sheets for both
                teams
        
        Returns:
            dict: Dict with game result and scores
        """            
        home_score = game_dict["Home"]["FPU"].sum() +1
        away_score = game_dict["Away"]["FPU"].sum() -1

        if abs(home_score-away_score):
            if home_score>away_score:
                result = "Home"
            if away_score>home_score:
                result = "Away"
        else:
            result = "Tie"

        result_dict = {"Home":home_score,
            "Away":away_score,
            "Result":result}
        
        return result_dict


    def process_game(self,game_dict):
        for key in game_dict.keys():
            # get already played games
            game_dict[key] = self.__process_team_performances(
                game_dict[key]
            )
        # calculate Fantasy Points
        endgame_dict = {}
        result = "uncertain"
        needed_extra_times = 0
        while result not in ["Home","Away"]:
            logger.info("Calculating earned FP using "+str(needed_extra_times)+" ET")
            for key in game_dict.keys():
                endgame_dict[key] = self.__calculate_fp(
                    team_sheet=game_dict[key],
                    no_of_extra_times=needed_extra_times
                )
            result_dict = self.__determine_winner(endgame_dict)
            result = result_dict["Result"]
            logger.info("Game result: "+str(result))
            needed_extra_times = needed_extra_times+1

        out_dict = {"game_dict":game_dict,
            "endgame_dict":endgame_dict,
            "result":result_dict}

        return out_dict


    

