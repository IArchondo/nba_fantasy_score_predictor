import logging

from g1_data_gathering.DataFetcher import DataFetcher
from g2_input_reader.MatchupReader import MatchupReader

logging.basicConfig(level=logging.INFO)

datafetch = DataFetcher()

datafetch.get_player_clean_gamelog("Bruce Brown")

[player for player in datafetch.nba_players_list if player[0]=="J"]

#datafetch.get_player_performance("Nikola Jokic",60)

matchupreader = MatchupReader()

out = matchupreader.read_given_excel("example_input.xlsx")

game = matchupreader.process_game(out)

game["Home"]

home = matchupreader.get_already_passed_games(out["Home"])

home


players_played = home[
    home["GAME_PLAYED"]==1
    ]["PLAYER_NAME"]

players_played

team_sheet = out["Home"].merge(
    right=home.loc[home["PLAYER_NAME"].isin(players_played),
    ["PLAYER_NAME","MIN","FP","FPPM"]],
    on=["PLAYER_NAME"],
    how="left"
)



performances = matchupreader.get_already_passed_games(out["Away"])

performances

import pandas as pd

test_df = pd.DataFrame({'MIN':[2,10,2,4,10],
    'POS':['G','G','GF','C','C'],
    'Order':[1,2,3,4,5],
    'Sec_order':[0,0,0,0,0],
    'FPPM':[1.2,0.2,0.9,0.4,0.6]})

positions = ['G','F','C']

new_columns = [['IM_'+pos,'UM_'+pos,'RM_'+pos] for pos in positions]

new_columns = [item for sublist in new_columns for item in sublist]

test_df = pd.concat([test_df,pd.DataFrame(columns=new_columns)],sort=False)

test_df.loc[:,['IM_G','RM_G']] = 10
test_df.loc[:,['IM_F','RM_F']] = 10
test_df.loc[:,['IM_C','RM_C']] = 10

test_df.loc[:,['UM_G','UM_F','UM_C']] = 0

## duplicate double position players
for i in range(len(test_df)):
    if len(test_df.loc[i,'POS'])>1:
        test_df.loc[len(test_df)+1,:] = test_df.loc[i,:]
        #split positions
        initial_position = test_df.loc[i,'POS'][0]
        secondary_position = test_df.loc[i,'POS'][1]
        test_df.loc[i,'POS'] = initial_position
        test_df.loc[len(test_df),'POS'] = secondary_position
        # assign hierarchy
        test_df.loc[i,'Sec_order'] = 1
        test_df.loc[len(test_df),'Sec_order'] = 2

#reorder to maintain general hierarchy
test_df = test_df.sort_values(['Order','Sec_order'])
test_df = test_df.reset_index(drop=True)

for i in range(len(test_df)):
    if i>0: 
        for pos in ['G','F','C']:
            test_df.loc[i,'IM_'+str(pos)] = test_df.loc[i-1,'RM_'+str(pos)] 
    used_position = test_df.loc[i,'POS'][0]
    if test_df.loc[i,'Sec_order']==2:
        test_df.loc[i,'MIN'] = test_df.loc[i,'MIN']-test_df.loc[i-1,
        [col for col in test_df.columns if 'UM' in col]].sum()
    if test_df.loc[i,'MIN']<=test_df.loc[i,'IM_'+str(used_position)]:
        test_df.loc[i,'UM_'+str(used_position)] = test_df.loc[i,'MIN']
        
    else:
        test_df.loc[i,'UM_'+str(used_position)] = (
            test_df.loc[i,'IM_'+str(used_position)])
        test_df.loc[i,'RM_'+str(used_position)] = 0

    for pos in positions:
            test_df.loc[i,'RM_'+str(pos)] = (
                test_df.loc[i,'IM_'+str(pos)]-
                test_df.loc[i,'UM_'+str(pos)])

test_df.loc[:,'UM'] = test_df.loc[:,
    [col for col in test_df.columns if 'UM' in col]].sum(axis=1)

test_df.loc[:,'FP'] = test_df['UM']*test_df['FPPM']

test_df