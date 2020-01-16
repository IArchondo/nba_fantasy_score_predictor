import logging
import pandas as pd
import numpy as np

from g1_data_gathering.DataFetcher import DataFetcher
from g3_performance_modeler.PerformanceModeler import PerformanceModeler

logger = logging.getLogger("MatchupCalculator")

class MatchupCalculator():
    def __init__(self,input_matchup):
        self.positions = ["G","F","C"]

        self.input_matchup = input_matchup
        
        self.datafetcher = DataFetcher()

        self.performance_modeler = PerformanceModeler()

    def assign_already_played_games(self,team_sheet):
        #TODO pasar al matchup calculator
        """Get all performances from games already played for
            a given team
        
        Args:
            team_sheet (pd.DataFrame): Team Sheet
        
        Returns:
            dict: Dict with gamelogs for all players and the complete performance_df
        """        
        
        logger.info("Gathering already existing performances...")            
        game_number = team_sheet["Game"][0]
        performance_list = []
        gamelog_dict = {}
        for player in team_sheet["Player"]:
            output_performance = self.datafetcher.get_player_performance(
                player_name=player,game_number=game_number
            )
            gamelog_dict[player] = output_performance["player_gamelog"]
            performance_list.append(output_performance["performance"])

        performance_df = pd.concat(performance_list)
        
        output_dict = {"gamelog_dict":gamelog_dict,
            "performance_df":performance_df}

        return output_dict

    ## utils
    def __group_player_double_position(self,x):
        d = {}
        d['Position'] = ''.join(x['Position'])
        d['MIN'] = x['MIN'].max()
        d['FP'] = x['FP'].max()
        d['IM_G'] = x['IM_G'].max()
        d['IM_F'] = x['IM_F'].max()
        d['IM_C'] = x['IM_C'].max()
        d['UM_G'] = x['UM_G'].sum()
        d['UM_F'] = x['UM_F'].sum()
        d['UM_C'] = x['UM_C'].sum()
        d['RM_G'] = x['RM_G'].min()
        d['RM_F'] = x['RM_F'].min()
        d['RM_C'] = x['RM_C'].min()
        d['UM'] = x['UM'].sum()
        d['FPU'] = x['FPU'].sum()

        return pd.Series(d,index=d.keys())

    

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

        #group players with double positions
        cols_to_group = ['Player','Game','Order','FPPM']

        grouped = team_sheet.groupby(cols_to_group).apply(self.__group_player_double_position).reset_index()

        grouped = grouped.sort_values('Order').reset_index(drop=True)

        grouped = grouped.loc[:,[col for col in team_sheet.columns if col!="Sec_order"]]

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

    def process_team_performances(self,team_sheet):
        """Assign already played games to a team sheet + save each player's
            gamelog in a dict
        
        Args:
            team_sheet (pd.DataFrame): Team sheet
        
        Returns:
            pd.DataFrame: Pandas dataframe with performances
        """        
        performance_output = self.assign_already_played_games(team_sheet)
        performance_table = performance_output["performance_df"]
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

        output_dict = {"team_sheet":team_sheet,
            "player_gamelogs":performance_output["gamelog_dict"]}

        return output_dict

    # def assign_performance_forecasts

    def __generate_game_scenarios(self,team_performances_dict,number_of_simulations=100):
        """Generate forecasts for all players that have not played yet
        
        Args:
            team_performances_dict (dict): Dict with team sheet and player gamelogs
            number_of_simulations (int, optional): Number of simulations
                to be executed. Defaults to 100.
        
        Returns:
            dict: Forecasts for all players that have not played yet
        """        
        
        player_forecasts = {}
        for key in team_performances_dict.keys():
            player_forecasts[key] = {}
            team_sheet = team_performances_dict[key]["team_sheet"]
            players_to_forecast = team_sheet[team_sheet["GAME_PLAYED"]!=1]["Player"].tolist()

            player_forecasts[key] = {player:self.performance_modeler.determine_forecast(
                player_gamelog = team_performances_dict[key]["player_gamelogs"][player],
                number_of_simulations=number_of_simulations
            )
            for player in players_to_forecast}

        return player_forecasts

    def __fill_gamesheet_with_forecast(self,processing_gamesheet,forecast_dict,simulation_number):
        """Insert a given prediction into a team sheet
        
        Args:
            processing_gamesheet (pd.DataFrame): Team sheet
            forecast_dict (dict): Dict with forecasts for all players
                that have not played yet
            simulation_number (int): Number of the simulation to be used
        
        Returns:
            pd.DataFrame: Dataframe with inserted forecasts
        """        

        filled_gamesheet = processing_gamesheet.copy()
        for player in forecast_dict.keys():
            ## insert forecasted minutes
            filled_gamesheet.loc[
                filled_gamesheet["Player"]==player,["MIN"]
                ] = forecast_dict[player]["minute_forecast"]

            ## insert forecasted fppm
            filled_gamesheet.loc[
                filled_gamesheet["Player"]==player,["FPPM"]
                ] = forecast_dict[player]["fppm_forecast"][simulation_number]

        return filled_gamesheet

    def process_game(self,game_dict):
        """Process a game dict in order to determine game winner
        
        Args:
            game_dict (dict): Dict with player sheets for home and away teams
        
        Returns:
            dict: Dict with original game_dict, filled game_dict and result
        """        
        
        # calculate Fantasy Points
        endgame_dict = {}
        result = "uncertain"
        needed_extra_times = 0
        while result not in ["Home","Away"]:
            logger.debug("Calculating earned FP using "+str(needed_extra_times)+" ET")
            for key in game_dict.keys():
                endgame_dict[key] = self.__calculate_fp(
                    team_sheet=game_dict[key],
                    no_of_extra_times=needed_extra_times
                )
            result_dict = self.__determine_winner(endgame_dict)
            result = result_dict["Result"]
            logger.debug("Game result: "+str(result))
            needed_extra_times = needed_extra_times+1

        out_dict = {"game_dict":game_dict,
            "endgame_dict":endgame_dict,
            "result":result_dict,
            "extra_times":needed_extra_times
        }

        return out_dict

    def __sum_up_results(self,game_outcomes):
        """Sum up results in a couple of basic measures
        
        Args:
            game_outcomes (list): list of simulated games
        
        Returns:
            dict: Dict with calculated measures
        """        
        logger.debug("Summing up results...")
        results = []
        victory_margin = []
        extra_times = []
        for i in range(len(game_outcomes)):
            results.append(game_outcomes[i]["result"]["Result"])
            victory_margin.append(abs(game_outcomes[i]["result"]["Home"]-game_outcomes[i]["result"]["Away"]))
            extra_times.append(game_outcomes[i]["extra_times"]>1)

        home_victories = sum([result=="Home" for result in results])
        away_victories = sum([result=="Away" for result in results])

        # home margin of victory
        average_home_margin = np.median(np.array(victory_margin)[[i for i,x in enumerate(results) if x=="Home"]])
        average_away_margin = np.median(np.array(victory_margin)[[i for i,x in enumerate(results) if x=="Away"]])

        if home_victories>away_victories:
            win_pct = round(home_victories/len(game_outcomes)*100,2)
            logger.info("\n--> Home won "+str(win_pct)+" percent of the simulated games!")
            logger.info("----> Its average winning margin was "+
                str(average_home_margin)+" FP")
        elif home_victories<away_victories:
            win_pct = round(away_victories/len(game_outcomes),2)*100
            logger.info("\n--> Away won "+str(win_pct)+" percent of the simulated games!")
            logger.info("----> Its average winning margin was "+
                str(average_home_margin)+" FP")
        else:
            logger.info("--> We have a tie!")
        
        amount_of_extra_times = sum(extra_times)
        logger.info(str(amount_of_extra_times)+" extra times were needed")

        output_results = {"home_victories":home_victories,
            "away_victories":away_victories,
            "average_home_margin":average_home_margin,
            "average_away_margin":average_away_margin,
            "amount_of_extra_times":amount_of_extra_times
            }

        return output_results

                    
    def generate_forecasts(self,game_dict,number_of_simulations=100):
        """Master execute for the whole class:
            - Gather information of already played games
            - Generate forecasts for players that have not played yet
            - Combine forecasts with already observed performances to simulate
                games
            - Sum up results

        Args:
            game_dict (dict): Dict with team sheets for home and away teams
            number_of_simulations (int, optional): Number of simulations
                to be executed. Defaults to 100.
        
        Returns:
            dict: Dict with all results
        """        
        
        logger.info("\nStep 1: Gathering NBA info")
        for key in game_dict.keys():
            # get already played games
            game_dict[key] = self.process_team_performances(
                game_dict[key]
            )
        ## generate game scenarios
        logger.info("\nStep 2: Generating forecasts for players where required")
        player_forecasts = self.__generate_game_scenarios(game_dict,number_of_simulations)

        ## fill forecasts with generated scenarios
        logger.info("\nStep 3: Filling in forecasts into game canvases")
        game_simulations = []
        for i in range(number_of_simulations):
            game_dict_output = {}
            for key in game_dict.keys():
                game_dict_output[key] = self.__fill_gamesheet_with_forecast(
                    processing_gamesheet=game_dict[key]["team_sheet"],
                    forecast_dict=player_forecasts[key],
                    simulation_number=i
                    )
            game_simulations.append(game_dict_output)

        ## determine outcome of each game
        logger.info("\nStep 4: Determining outcomes of simulated games")
        game_outcomes = [self.process_game(game_simulations[game_no])
            for game_no in range(len(game_simulations))]

        ## sum up results
        logger.info("\nStep 5: Summing up results")
        results_summary = self.__sum_up_results(game_outcomes)

        output_dict = {"results_summary":results_summary,
            "simulated_games":game_outcomes,
            "player_forecasts":player_forecasts,
            "game_dict":game_dict}
        
        return output_dict


    


    

