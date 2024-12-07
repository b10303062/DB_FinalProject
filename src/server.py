import sys
import argparse
import psycopg
from psycopg import Cursor
from psycopg.rows import dict_row
import socket
import threading
import json
import datetime
from display_utils import *
from network_utils import *

RETCODE_NORMAL = 1
RETCODE_EXIT = 0
RETCODE_ERROR = -1

BUFFER_MAXLEN = 4096

# Record all clients' sockets
client_id2sock = {}

# PostgreSQL connection
pg_conn = psycopg.connect(
    host = "localhost",
    port = 5432,
    user = "postgres",
    password = "postgres",
    dbname = "Steam-Together-fortest"
)

REQUEST_MAP = {
    "exit": 0,
    "sign in": 1,
    "sign up": 2,
    "search games": 3,
    "add review": 4,
    "delete review": 5,
    "add to favorite": 6,
    "create room": 7,
    "join room": 8,
    "check user": 9,
    "update profile": 10,
    "list rooms": 11,
    "check reviews": 12,
    "room communication": 13,
    "leave room": 14
}

def _user_exit(request: dict, cursor: Cursor, client_sock: socket.socket):
    user_id = request["userID"]
    client_id2sock.pop(user_id)

def _user_sign_in(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        query = """
                SELECT "user_name", "password" 
                FROM "user"
                WHERE "user_id" = {};
                """.format(user_id)
        cursor.execute(query)
        row = cursor.fetchone()
        
        if not row:
            response = {
                "status": "FAIL",
                "errorMessage": "User not found"
            }
        else:
            user_name, password = row["user_name"], row["password"]
            if request["password"] == password:
                query = """
                        SELECT "role" 
                        FROM "user_role" 
                        WHERE "user_id" = {};
                        """.format(user_id)
                cursor.execute(query)
                row = cursor.fetchone()
                role = row["role"]
                response = {
                    "status": "OK",
                    "userName": user_name,
                    "role": role
                }
            else:
                response = {
                    "status": "FAIL",
                    "errorMessage": "Authentication failed"
                }

            client_id2sock[user_id] = client_sock
        
        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }

    sendall(client_sock, response)

def _user_sign_up(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_name = request["userName"].replace("\'", "\'\'")
        email = request["email"].replace("\'", "\'\'")
        password = request["password"].replace("\'", "\'\'")
        role = request["role"]
        join_date = str(datetime.date.today())

        query = """
                INSERT INTO "user" ("user_name", "email", "password", "join_date") 
                VALUES ('{}', '{}', '{}', '{}')
                RETURNING "user_id";
                """.format(user_name, email, password, join_date)
        cursor.execute(query)
        user_id = cursor.fetchone()["user_id"]

        query = """
                INSERT INTO "user_role" ("user_id", "role")
                VALUES ({}, '{}');
                """.format(user_id, role)
        cursor.execute(query)
        
        response = {
            "status": "OK",
            "userID": user_id
        }

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
    
    sendall(client_sock, response)

def _user_search_games(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_name = request.get("gameName")
        genres = request.get("genres")
        price_low = request.get("priceLow")
        price_upp = request.get("priceUpp")
        
        query = """
                SELECT 
                    "g"."game_id", 
                    "game_name", 
                    "release_date", 
                    "total_achievements", 
                    "positive_ratings", 
                    "negative_ratings", 
                    "genre"
                FROM "game" AS "g"
                    JOIN "game_genre" AS "gg" ON "g"."game_id" = "gg"."game_id"
                WHERE"""
        conditions = [" true "]
        if game_name:
            conditions.append(""" LOWER("game_name") LIKE LOWER('%{}%') """.format(game_name))
        if genres:
            conditions.append(""" "genre" IN ('{}') """.format("','".join(genres)))
        if price_low:
            conditions.append(""" "price" >= {} """.format(price_low))
        if price_upp:
            conditions.append(""" "price" <= {} """.format(price_upp))
        query += "AND".join(conditions) + ';'
        cursor.execute(query)
        rows = cursor.fetchall()

        response = {
            "status": "OK",
            "data": []
        }
        gameid2idx = {}
        for row in rows:
            idx = gameid2idx.get(row["game_id"])
            if idx is None:
                response["data"].append({
                    "gameID": row["game_id"],
                    "gameName": row["game_name"],
                    "genres": [row["genre"]],
                    "releaseDate": str(row["release_date"]),
                    "totalAchievements": row["total_achievements"],
                    "positiveRatings": row["positive_ratings"],
                    "negativeRatings": row["negative_ratings"]
                })
                gameid2idx[row["game_id"]] = len(response["data"]) - 1
            else:
                response["data"][idx]["genres"].append(row["genre"])

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
    
    sendall(client_sock, response)

def _user_add_reviews(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        game_id = request["gameID"]
        review_text = request["reviewText"]
        review_rating = request["reviewRating"]

        query = """
                SELECT COUNT(*)
                FROM "review"
                WHERE "user_id" = {} AND "game_id" = {};
                """.format(user_id, game_id)
        cursor.execute(query)
        count = cursor.fetchone()["count"]

        if count == 1:
            response = {
                "status": "FAIL",
                "errorMessage": "You already review on the game."
            }

            pg_conn.rollback()
        else:
            current_time = str(datetime.datetime.now().replace(microsecond = 0))
            query = """
                    INSERT INTO "review" ("user_id", "game_id", "times", "texts", "rating")
                    VALUES ({}, {}, '{}', '"{}"', {});
                    """.format(user_id, game_id, current_time, review_text, review_rating)
            cursor.execute(query)

            response = {
                "status": "OK"
            }

            pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }
        
    sendall(client_sock, response)

def _user_delete_reviews(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        game_id = request["gameID"]

        query = """
                DELETE FROM "review"
                WHERE "user_id" = {} AND "game_id" = {};
                """.format(user_id, game_id)
        cursor.execute(query)

        response = {
            "status": "OK"
        }

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }

    sendall(client_sock, response)

def _user_add_to_favorites(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        game_id = request["gameID"]

        query = """
                SELECT COUNT(*)
                FROM "add_to_favorite"
                WHERE "user_id" = {} AND "game_id" = {};
                """.format(user_id, game_id)
        cursor.execute(query)
        existed = cursor.fetchone()["count"]

        if not existed:
            query = """
                    INSERT INTO "add_to_favorite" ("user_id", "game_id")
                    VALUES ({}, {});
                    """.format(user_id, game_id)
            cursor.execute(query)

            response = {
                "status": "OK"
            }

            pg_conn.commit()
        else:
            response = {
                "status": "FAIL",
                "errorMessage": "The game is in your favorites already"
            }

            pg_conn.rollback()
         
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }

    sendall(client_sock, response)

def _user_create_room(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        room_name = request["roomName"].replace("\'", "\'\'")
        game_id = request["gameID"]
        start_datetime = str(datetime.datetime.now().replace(microsecond=0))

        query = """
                INSERT INTO "room" ("creator_id", "room_name", "game_id", "start_time", "status")
                VALUES ({}, '{}', {}, '{}', '{}')
                RETURNING "room_id";
                """.format(user_id, room_name, game_id, start_datetime, "Active")
        cursor.execute(query)
        room_id = cursor.fetchone()["room_id"]

        query = """
                INSERT INTO "user_in_room" ("user_id", "room_id", "join_time")
                VALUES ({}, {}, '{}');
                """.format(user_id, room_id, start_datetime)
        cursor.execute(query)

        query = """
                SELECT "game_name"
                FROM "game"
                WHERE "game_id" = {};
                """.format(game_id)
        cursor.execute(query)
        game_name = cursor.fetchone()["game_name"]

        if game_name:
            response = {
                "status": "OK",
                "roomID": room_id,
                "gameName": game_name
            }
            pg_conn.commit()
        else:
            response = {
                "status": "FAIL",
                "errorMessage": "Game not found."
            }
            pg_conn.rollback()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }

    sendall(client_sock, response)

def _user_join_room(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        room_id = request["roomID"]
        join_time = str(datetime.datetime.now().replace(microsecond=0))

        query = """
                SELECT "status"
                FROM "room"
                WHERE "room_id" = {}
                """.format(room_id)
        cursor.execute(query)
        status = cursor.fetchone()["status"]

        if status == "Active":
            query = """
                    SELECT "user_id", "room_id"
                    FROM "user_in_room"
                    WHERE "user_id" = {} AND "room_id" = {};
                    """.format(user_id, room_id)
            cursor.execute(query)
            row = cursor.fetchone()

            if not row:
                query = """
                        INSERT INTO "user_in_room" ("user_id", "room_id", "join_time")
                        VALUES ({}, {}, '{}');
                        """.format(user_id, room_id, join_time)
            else:
                query = """
                        UPDATE "user_in_room"
                        SET "join_time" = '{}', "leave_time" = NULL
                        WHERE "user_id" = {} AND "room_id" = {};
                        """.format(join_time, user_id, room_id)
            cursor.execute(query)

            query = """
                    SELECT "r"."room_name", "u"."user_name", "g"."game_name"
                    FROM "room" AS "r"
                        JOIN "user" AS "u" ON "u"."user_id" = "r"."creator_id"
                        JOIN "game" AS "g" ON "g"."game_id" = "r"."game_id"
                    WHERE "room_id" = {};
                    """.format(room_id)
            cursor.execute(query)
            row =  cursor.fetchone()
            room_name = row["room_name"]
            room_host = row["user_name"]
            game_name = row["game_name"]

            response = {
                "status": "OK",
                "roomName": room_name,
                "roomHost": room_host,
                "gameName": game_name
            }

            pg_conn.commit()

        elif status == "Closed":
            response = {
                "status": "FAIL",
                "errorMessage": "Room not found"
            }

        else:
            raise Exception("Room has invalid status value.")

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }

    sendall(client_sock, response)

def _user_check_user(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]

        query = """
                SELECT "user_id", "user_name", "join_date"
                FROM "user"
                WHERE "user_id" = {};
                """.format(user_id)
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            user_name = row["user_name"]
            join_date = str(row["join_date"])
            response = {
                "status": "OK",
                "userInfo": {
                    "id": user_id,
                    "name": user_name,
                    "joinDate": join_date,
                    "favorites": []
                }
            }

            query = """
                    SELECT "g"."game_id", "g"."game_name"
                    FROM "add_to_favorite" AS "f"
                        JOIN "game" AS "g" ON "f"."game_id" = "g"."game_id"
                    WHERE "f"."user_id" = {};
                    """.format(user_id)
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                response["userInfo"]["favorites"].append({
                    "gameID": row["game_id"],
                    "gameName": row["game_name"]
                })

        else:
            response = {
                "status": "FAIL",
                "errorMessage": "User not found"
            }

    except Exception as e:
        print("[Error] {}".format(e))

    sendall(client_sock, response)

def _user_update_profile(request: dict, cursor: Cursor, client_sock: socket.socket):
    user_id = request["userID"]
    new_name = request["updated"].get("name")
    new_email = request["updated"].get("email")
    new_password = request["updated"].get("password")

    query = """
            UPDATE "user"
            SET {{}}
            WHERE "user_id" = {0}
            """.format(user_id)
    updates = []
    if new_name:
        updates.append("\"user_name\" = \'{}\'".format(new_name))
    if new_email:
        updates.append("\"email\" = \'{}\'".format(new_email))
    if new_password:
        updates.append("\"password\" = \'{}\'".format(new_password))
    
    if len(updates) == 0:
        response = {
            "status": "FAIL",
            "errorMessage": "Nothing to do"
        }
    else:
        try:
            query = query.format(", ".join(updates))
            cursor.execute(query)
            query = """
                    SELECT "user_name", "email"
                    FROM "user"
                    WHERE "user_id" = {};
                    """.format(user_id)
            cursor.execute(query)
            row = cursor.fetchone()
            name = row["user_name"]
            email = row["email"]

            response = {
                "status": "OK",
                "userProfile": {
                    "name": name,
                    "email": email
                }
            }

            pg_conn.commit()
            
        except Exception as e:
            pg_conn.rollback()
            print("[Error] {}".format(e))
            response = {
                "status": "FAIL",
                "errorMessage": "Unknown error"
            }

    sendall(client_sock, response)

def _user_list_rooms(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_id = request.get("gameID")

        query = """
                SELECT "r"."room_id", "r"."room_name", "g"."game_name", "r"."creator_id", "u"."user_name"
                FROM "room" AS "r" 
                    JOIN "user" AS "u" ON "r"."creator_id" = "u"."user_id"
	                JOIN "game" AS "g" ON "r"."game_id" = "g"."game_id"
                WHERE "r"."status" = 'Active' """
        if game_id:
            query += """ AND "r"."game_id" = {}""".format(game_id)
        cursor.execute(query)
        rows = cursor.fetchall()

        response = {
            "status": "OK",
            "rooms": []
        }
        for row in rows:
            response["rooms"].append({
                "roomID": row["room_id"],
                "roomName": row["room_name"],
                "playGame": row["game_name"],
                "hostID": row["creator_id"],
                "hostName": row["user_name"]
            })
    
    except Exception as e:
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }

    sendall(client_sock, response)

def _user_check_reviews(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request.get("userID")
        game_id = request["gameID"]
        rating = request.get("rating")

        query = """
                SELECT "user_id", "texts", "rating"
                FROM "review"
                WHERE "game_id" = {}""".format(game_id)
        if user_id:
            query += """ AND "user_id" = {}""".format(user_id)
        if rating:
            query += """ AND "rating" = {}""".format(rating)
        cursor.execute(query)
        rows = cursor.fetchall()

        response = {
            "status": "OK",
            "reviews": []
        }
        for row in rows:
            response["reviews"].append({
                "userID": row["user_id"],
                "reviewText": row["texts"],
                "reviewRating": row["rating"]
            })

    except Exception as e:
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
    
    sendall(client_sock, response)

def _user_room_communication(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        room_id = request["roomID"]
        sender_id = request["fromUserID"]
        timestamp = request["timestamp"]
        content = request["content"]

        query = """
                SELECT "user_name"
                FROM "user"
                WHERE "user_id" = {};
                """.format(sender_id)
        cursor.execute(query)
        sender_name = cursor.fetchone()["user_name"]
        
        response_sender = {
            "status": "OK"
        }

        response_broadcast = {
            "status": "OK",
            "messageType": "room communication",
            "fromUserID": sender_id,
            "fromUserName": sender_name,
            "timestamp": timestamp,
            "content": content
        }

        query = """
                SELECT "user_id"
                FROM "user_in_room"
                WHERE "room_id" = {};
                """.format(room_id)
        cursor.execute(query)
        rows = cursor.fetchall()

    except Exception as e:
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)
        return

    sendall(client_sock, response_sender)
    for row in rows:
        if row["user_id"] != sender_id:
            sendall(client_id2sock[row["user_id"]], response_broadcast)

def _user_leave_room(request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        room_id = request["roomID"]
        leave_time = str(datetime.datetime.now().replace(microsecond=0))

        query = """
                SELECT "creator_id"
                FROM "room"
                WHERE "room_id" = {}
                """.format(room_id)
        cursor.execute(query)
        room_host_id = cursor.fetchone()["creator_id"]

        query = """
                UPDATE "user_in_room"
                SET "leave_time" = '{}'
                WHERE "user_id" = {} AND "room_id" = {};
                """.format(leave_time, user_id, room_id)
        cursor.execute(query)

        response = {
            "status": "OK"
        }
        
        if room_host_id == user_id:
            response_broadcast = {
                "status": "OK",
                "messageType": "room control",
                "action": "leave"
            }

            query = """
                    SELECT "user_id", "leave_time"
                    FROM "user_in_room"
                    WHERE "room_id" = {};
                    """.format(room_id)
            cursor.execute(query)
            rows = cursor.fetchall()

            end_time = str(datetime.datetime.now().replace(microsecond=0))
            query = """
                    UPDATE "room"
                    SET "end_time" = '{}', "status" = 'Closed'
                    WHERE "room_id" = {};
                    """.format(end_time, room_id)
            cursor.execute(query)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }

    sendall(client_sock, response)
    if room_host_id == user_id:
        for row in rows:
            if row["user_id"] != user_id and not row["leave_time"]:
                sendall(client_id2sock[row["user_id"]], response_broadcast)

def handle_request(request: dict, cursor: Cursor, client_sock: socket.socket) -> int:
    request_id = REQUEST_MAP[request["requestType"]]
    match request_id:
        case 0:
            _user_exit(request, cursor, client_sock)
            return RETCODE_EXIT
        case 1:
            _user_sign_in(request, cursor, client_sock)
        case 2:
            _user_sign_up(request, cursor, client_sock)
        case 3:
            _user_search_games(request, cursor, client_sock)
        case 4:
            _user_add_reviews(request, cursor, client_sock)
        case 5:
            _user_delete_reviews(request, cursor, client_sock)
        case 6:
            _user_add_to_favorites(request, cursor, client_sock)
        case 7:
            _user_create_room(request, cursor, client_sock)
        case 8:
            _user_join_room(request, cursor, client_sock)
        case 9:
            _user_check_user(request, cursor, client_sock)
        case 10:
            _user_update_profile(request, cursor, client_sock)
        case 11:
            _user_list_rooms(request, cursor, client_sock)
        case 12:
            _user_check_reviews(request, cursor, client_sock)
        case 13:
            _user_room_communication(request, cursor, client_sock)
        case 14:
            _user_leave_room(request, cursor, client_sock)
        case _:
           return RETCODE_ERROR

    return RETCODE_NORMAL    

def handle_client(client_sock: socket.socket, client_addr):
    try:
        cursor = pg_conn.cursor(row_factory = dict_row)
        while True:
            recv_data = client_sock.recv(BUFFER_MAXLEN)
            if len(recv_data) > 0:
                request = json.loads(recv_data)
                retcode = handle_request(request, cursor, client_sock)
            if retcode == RETCODE_ERROR:
                print("[Error] Failed to handle the request. Abort the client connection.")
                break
            elif retcode == RETCODE_EXIT:
                print("[Log] Client at {}:{} exited.".format(client_addr[0], client_addr[1]))
                break

    finally:
        client_sock.close()
        cursor.close()
        exit(0)

def main(args):
    host = "127.0.0.1"
    port = args.port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(8)

    clear_screen()
    print("Listening at port {}".format(port))
    
    try:
        while True:
            client_sock, client_addr = sock.accept()
            print("[Log] Accept connection from {}:{}".format(client_addr[0], client_addr[1]))

            t = threading.Thread(target = handle_client, args = (client_sock, client_addr))
            t.daemon = True
            t.start()

    finally:
        sock.close()
        pg_conn.close()
        clear_screen()
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type = int, help = "Specify the port to listen on. (default = 8888)", default = 8888)
    args = parser.parse_args()
    main(args)