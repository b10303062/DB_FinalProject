import argparse
import time 
import random
import pandas as pd
from collections import defaultdict

"""
-----------------------------------
GAME_PROMOTION
-----------------------------------
game_id                 PK
promotion_id            PK
-----------------------------------
"""

def main(args):
    raw_game_data = pd.read_csv(args.game_input)
    raw_promotion_data = pd.read_csv(args.prom_input).sort_values("Start_time").reset_index()
    game_promotion_data = pd.DataFrame(columns = ["game_id", "promotion_id"])

    promid2row = {}
    for i in range(len(raw_promotion_data)):
        promid2row[raw_promotion_data.iloc[i]["Promotion_id"]] = i

    game_promotion = defaultdict(list)
    for game_id in raw_game_data["appid"]:
        for i in range(len(raw_promotion_data)):
            promotion = raw_promotion_data.iloc[i]
            if random.random() < args.promotion_prob:
                if len(game_promotion[game_id]) == 0 or \
                   str(promotion["Start_time"]) > raw_promotion_data.iloc[promid2row[game_promotion[game_id][-1]]]["End_time"]:
                    game_promotion[game_id].append(int(promotion["Promotion_id"]))
    
    for game_id in game_promotion:
        for promotion in game_promotion[game_id]:
            game_promotion_data = pd.concat([game_promotion_data, pd.DataFrame([[game_id, promotion]], columns = game_promotion_data.columns)])

    dest_path = args.output
    print("Writing to {} ...".format(dest_path), end = "")
    game_promotion_data.to_csv(dest_path, index = False)
    print(" done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("game_input", type = str, help = "Path to the input csv file including the games")
    parser.add_argument("prom_input", type = str, help = "Path to the input csv file including the promotions")
    parser.add_argument("-p", "--promotion_prob", type = float, help = "The probability that a game participates in a promotion if it hasn't participated any.", default = 0.3)
    parser.add_argument("-o", "--output", type = str, help = "Path for the output csv file.", default = "./table_game_promotion.csv")
    args = parser.parse_args()
    
    start = time.time()
    main(args)
    end = time.time()

    print("Time elapsed: {} seconds".format(end - start))