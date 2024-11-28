import argparse
import time 
import pandas as pd

"""
-----------------------------------
GAME
-----------------------------------
game_id                 PK
game_name
release_date
price
toal_achievements
positive_ratings
negative_ratings
-----------------------------------
"""

def main(args):
    raw_game_data = pd.read_csv(args.input)
    game_data = pd.DataFrame()
    game_data["game_id"] = raw_game_data["appid"]
    game_data["game_name"] = raw_game_data["name"]
    game_data["release_date"] = raw_game_data["release_date"]
    game_data["price"] = raw_game_data["price"]
    game_data["total_achievements"] = raw_game_data["achievements"]
    game_data["positive_ratings"] = raw_game_data["positive_ratings"]
    game_data["negative_ratings"] = raw_game_data["negative_ratings"]

    dest_path = args.output
    print("Writing to {} ...".format(dest_path), end = "")
    game_data.to_csv(dest_path, index = False)
    print(" done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type = str, help = "Path to the input csv file")
    parser.add_argument("-o", "--output", type = str, help = "Path for the output csv file.", default = "./table_game.csv")
    args = parser.parse_args()
    
    start = time.time()
    main(args)
    end = time.time()

    print("Time elapsed: {} seconds".format(end - start))