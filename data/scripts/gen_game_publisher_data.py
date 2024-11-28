import argparse
import time
import pandas as pd

"""
------------------------------------------------------
GAME_PUBLISHER
------------------------------------------------------
game_id         FK: GAME(game_id)           PK
publisher                                   PK
------------------------------------------------------
"""

def main(args):
    raw_game_data = pd.read_csv(args.input)
    game_publisher_data = pd.DataFrame(columns = ["game_id", "publisher"])

    for i in range(len(raw_game_data)):
        id = raw_game_data["appid"][i]
        for publisher in set(str(raw_game_data["publisher"][i]).split(";")):
            game_publisher_data = pd.concat([game_publisher_data, pd.DataFrame([[id, publisher]], columns = game_publisher_data.columns)])


    dest_path = args.output
    print("Writing to {} ...".format(dest_path), end = "")
    game_publisher_data.to_csv(dest_path, index = False)
    print(" done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type = str, help = "Path to the input csv file")
    parser.add_argument("-o", "--output", type = str, help = "Path for the output csv file.", default = "./table_game_publisher.csv")
    args = parser.parse_args()
    
    start = time.time()
    main(args)
    end = time.time()

    print("Time elapsed: {} seconds".format(end - start))