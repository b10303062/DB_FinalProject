import argparse
import time
import pandas as pd

"""
--------------------------------------------------------------
GAME_GENRE
--------------------------------------------------------------
game_id         FK: GAME(game_id)           PK
game_genre                                  PK
--------------------------------------------------------------
"""

def main(args):
    raw_game_data = pd.read_csv(args.input)
    game_genre_data = pd.DataFrame(columns = ["game_id", "genre"])

    for i in range(len(raw_game_data)):
        game_id = raw_game_data["appid"][i]
        for genre in set(str(raw_game_data["genres"][i]).split(";")):
            game_genre_data = pd.concat([game_genre_data, pd.DataFrame([[game_id, genre]], columns = game_genre_data.columns)])

    dest_path = args.output
    print("Writing to {} ...".format(dest_path), end = "")
    game_genre_data.to_csv(dest_path, index = False)
    print(" done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type = str, help = "Path to the input csv file")
    parser.add_argument("-o", "--output", type = str, help = "Path for the output csv file.", default = "./table_game_genre.csv")
    args = parser.parse_args()
    
    start = time.time()
    main(args)
    end = time.time()

    print("Time elapsed: {} seconds".format(end - start))