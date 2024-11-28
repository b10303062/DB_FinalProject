import argparse
import time
import pandas as pd

"""
-------------------------------------------------------
GAME_PLATFORM
-------------------------------------------------------
game_id         FK: GAME(game_id)           PK
platform                                    PK
-------------------------------------------------------
"""

def main(args):
    raw_game_data = pd.read_csv(args.input)
    game_platform_data = pd.DataFrame(columns = ["game_id", "platform"])

    for i in range(len(raw_game_data)):
        game_id = raw_game_data["appid"][i]
        for platform in set(str(raw_game_data["platforms"][i]).split(";")):
            game_platform_data = pd.concat([game_platform_data, pd.DataFrame([[game_id, platform]], columns = game_platform_data.columns)])

    dest_path = args.output
    print("Writing to {} ...".format(dest_path), end = "")
    game_platform_data.to_csv(dest_path, index = False)
    print(" done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type = str, help = "Path to the input csv file")
    parser.add_argument("-o", "--output", type = str, help = "Path for the output csv file.", default = "./table_game_platform.csv")
    args = parser.parse_args()
    
    start = time.time()
    main(args)
    end = time.time()

    print("Time elapsed: {} seconds".format(end - start))