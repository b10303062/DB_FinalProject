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

join_room_lock = threading.Lock()

# Record all clients' sockets
client_id2sock = {}

# PostgreSQL connection settings
PG_HOST = None 
PG_PORT = None
PG_USER = None
PG_PASSWORD = None
PG_DBNAME = None
ISOLATION_LEVEL = 3

REQUEST_MAP = {
    # General functions
    "exit": 0,
    "sign in": 1,
    "sign up": 2,
    # User functions
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
    "leave room": 14,
    # Admin functions
    "add game": 15,
    "update game": 16,
    "delete game": 17,
    "setup promotion": 18
}

def _exit(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    user_id = request["userID"]
    client_id2sock.pop(user_id)

def _sign_in(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

            if not client_id2sock.get(user_id):
                client_id2sock[user_id] = client_sock
            else:
                response = {
                    "status": "FAIL",
                    "errorMessage": "You have already signed in somewhere."
                }

        sendall(client_sock, response)
        
        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }
        sendall(client_sock, response)

def _sign_up(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

        sendall(client_sock, response)

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _user_search_games(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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
                    "releaseDate": str(row["release_date"]) if row["release_date"] is not None else "",
                    "totalAchievements": row["total_achievements"] if row["total_achievements"] is not None else "",
                    "positiveRatings": row["positive_ratings"] if row["positive_ratings"] is not None else "",
                    "negativeRatings": row["negative_ratings"] if row["negative_ratings"] is not None else ""
                })
                gameid2idx[row["game_id"]] = len(response["data"]) - 1
            else:
                response["data"][idx]["genres"].append(row["genre"])

        sendall(client_sock, response)

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)
    
def _user_add_reviews(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

            if review_rating >= 4:
                query = """
                        SELECT "genre"
                        FROM "game_genre"
                        WHERE "game_id" = {};
                        """.format(game_id)
                cursor.execute(query)
                genres = [row["genre"] for row in cursor.fetchall()]
                if genres:
                    query = """
                            SELECT g."game_id", g."game_name", g."positive_ratings"
                            FROM "game" g
                            JOIN "game_genre" gg ON g."game_id" = gg."game_id"
                            WHERE gg."genre" IN ('{}') AND g."game_id" != {}
                            GROUP BY g."game_id"
                            ORDER BY g."positive_ratings" DESC
                            LIMIT 5;
                            """.format("','".join(genres), game_id)
                    cursor.execute(query)
                    recommendations = cursor.fetchall()
                    response["recommendations"] = [
                        {"gameID": row["game_id"], "gameName": row["game_name"], "positiveRatings": row["positive_ratings"]}
                        for row in recommendations
                    ]

        sendall(client_sock, response)
        
        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }
        sendall(client_sock, response)
        
def _user_delete_reviews(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _user_add_to_favorites(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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
        
        else:
            response = {
                "status": "FAIL",
                "errorMessage": "The game is in your favorites already"
            }

        sendall(client_sock, response)

        pg_conn.commit()
         
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _user_create_room(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        user_id = request["userID"]
        room_name = request["roomName"].replace("\'", "\'\'")
        game_id = request["gameID"]
        max_members = request["roomNumMembersLimit"] 
        start_datetime = str(datetime.datetime.now().replace(microsecond=0))

        query = """
                INSERT INTO "room" ("creator_id", "room_name", "game_id", "start_time", "status", "max_players")
                VALUES ({}, '{}', {}, '{}', '{}', {})
                RETURNING "room_id";
                """.format(user_id, room_name, game_id, start_datetime, "Active", max_members)
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

        else:
            response = {
                "status": "FAIL",
                "errorMessage": "Game not found."
            }

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _user_join_room(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    join_room_lock.acquire()

    try:
        user_id = request["userID"]
        room_id = request["roomID"]
        join_time = str(datetime.datetime.now().replace(microsecond=0))

        query = """
                SELECT "status", "max_players"
                FROM "room"
                WHERE "room_id" = {};
                """.format(room_id)
        cursor.execute(query)
        row = cursor.fetchone()

        room_found = row and row["status"] == "Active"
        if not room_found:
            response = {
                "status": "FAIL",
                "errorMessage": "Room not found"
            }
            sendall(client_sock, response)
        
        else:
            room_found = True
            max_members = row["max_players"]
            
            query = """
                    SELECT COUNT(*)
                    FROM "user_in_room"
                    WHERE "room_id" = {} AND "leave_time" IS NULL;
                    """.format(room_id)
            cursor.execute(query)
            n_members = cursor.fetchone()["count"]

            if n_members < max_members:
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
                        SELECT "r"."room_name", "r"."max_players", "u"."user_name", "g"."game_name"
                        FROM "room" AS "r"
                            JOIN "user" AS "u" ON "u"."user_id" = "r"."creator_id"
                            JOIN "game" AS "g" ON "g"."game_id" = "r"."game_id"
                        WHERE "room_id" = {};
                        """.format(room_id)
                cursor.execute(query)
                row =  cursor.fetchone()
                room_name = row["room_name"]
                max_members = row["max_players"]
                room_host = row["user_name"]
                game_name = row["game_name"]

                query = """
                        SELECT "user_id", "leave_time"
                        FROM "user_in_room"
                        WHERE "room_id" = {} AND "leave_time" IS NULL;
                        """.format(room_id)
                cursor.execute(query)
                users_in_room = cursor.fetchall()

                response = {
                    "status": "OK",
                    "roomName": room_name,
                    "roomHost": room_host,
                    "roomNumMembers": len(users_in_room),
                    "roomNumMembersLimit": max_members,
                    "gameName": game_name
                }

                query = """
                        SELECT "user_name"
                        FROM "user"
                        WHERE "user_id" = {};
                        """.format(user_id)
                cursor.execute(query)
                user_name = cursor.fetchone()["user_name"]

                response_broadcast = {
                    "status": "OK",
                    "messageType": "room control",
                    "event": "join",
                    "userID": user_id,
                    "userName": user_name
                }

                sendall(client_sock, response)
                if room_found:
                    for user in users_in_room:
                        if user["user_id"] != user_id:
                            sendall(client_id2sock[user["user_id"]], response_broadcast)
            
            else:
                response = {
                    "status": "FAIL",
                    "errorMessage": "The room is full now"
                }
                sendall(client_sock, response)       
        
        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)
    
    join_room_lock.release()

def _user_check_user(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }
        sendall(client_sock, response)

def _user_update_profile(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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
        sendall(client_sock, response)
    
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

            sendall(client_sock, response)

            pg_conn.commit()
            
        except Exception as e:
            pg_conn.rollback()
            print("[Error] {}".format(e))
            response = {
                "status": "FAIL",
                "errorMessage": "Unknown error"
            }
            sendall(client_sock, response)

def _user_list_rooms(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_id = request.get("gameID")

        query = """
                SELECT "r"."room_id", "r"."room_name", "g"."game_name", "r"."creator_id", "u"."user_name", "r"."max_players"
                FROM "room" AS "r" 
                    JOIN "user" AS "u" ON "r"."creator_id" = "u"."user_id"
	                JOIN "game" AS "g" ON "r"."game_id" = "g"."game_id"
                WHERE "r"."status" = 'Active' """
        if game_id:
            query += """ AND "r"."game_id" = {}""".format(game_id)
        cursor.execute(query)
        rooms = cursor.fetchall()

        for room in rooms:
            query = """
                    SELECT COUNT(*)
                    FROM "user_in_room"
                    WHERE "room_id" = {} AND "leave_time" IS NULL;
                    """.format(room["room_id"])
            cursor.execute(query)
            room["roomNumMembers"] = cursor.fetchone()["count"]

        response = {
            "status": "OK",
            "rooms": []
        }
        for room in rooms:
            response["rooms"].append({
                "roomID": room["room_id"],
                "roomName": room["room_name"],
                "playGame": room["game_name"],
                "hostID": room["creator_id"],
                "hostName": room["user_name"],
                "roomNumMembers": room["roomNumMembers"],
                "roomNumMembersLimit": room["max_players"]
            })

        sendall(client_sock, response)

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknwon error"
        }
        sendall(client_sock, response)

def _user_check_reviews(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)
    
def _user_room_communication(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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
                SELECT "user_id", "leave_time"
                FROM "user_in_room"
                WHERE "room_id" = {};
                """.format(room_id)
        cursor.execute(query)
        users_in_room = cursor.fetchall()

        sendall(client_sock, response_sender)
        for user in users_in_room:
            if user["user_id"] != sender_id and not user["leave_time"]:
                sendall(client_id2sock[user["user_id"]], response_broadcast)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _user_leave_room(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
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

        query = """
                SELECT "user_name"
                FROM "user"
                WHERE "user_id" = {};
                """.format(user_id)
        cursor.execute(query)
        user_name = cursor.fetchone()["user_name"]

        response_broadcast_leave = {
            "status": "OK",
            "messageType": "room control",
            "event": "leave",
            "userID": user_id,
            "userName": user_name
        }

        query = """
                SELECT "user_id", "leave_time"
                FROM "user_in_room"
                WHERE "room_id" = {} AND "leave_time" IS NULL;
                """.format(room_id)
        cursor.execute(query)
        users_in_room = cursor.fetchall()
        
        if room_host_id == user_id:
            response_broadcast_close = {
                "status": "OK",
                "messageType": "room control",
                "event": "close"
            }

            for user in users_in_room:
                query = """
                UPDATE "user_in_room"
                SET "leave_time" = '{}'
                WHERE "user_id" = {} AND "room_id" = {};
                """.format(leave_time, user["user_id"], room_id)
                cursor.execute(query)
            
            end_time = str(datetime.datetime.now().replace(microsecond=0))
            query = """
                    UPDATE "room"
                    SET "end_time" = '{}', "status" = 'Closed'
                    WHERE "room_id" = {};
                    """.format(end_time, room_id)
            cursor.execute(query)

        sendall(client_sock, response)
        for user in users_in_room:
            if user["user_id"] != user_id:
                if room_host_id == user_id:
                    sendall(client_id2sock[user["user_id"]], response_broadcast_close)
                else:
                    sendall(client_id2sock[user["user_id"]], response_broadcast_leave)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _admin_add_game(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_name = request["gameName"].replace("\'", "\'\'")
        genres = request.get("genres")
        release_date = request["releaseDate"]
        price = request.get("price")
        total_achievements = request.get("totalAchievements")
        positive_ratings = request.get("positiveRatings")
        negative_ratings = request.get("negativeRatings")

        query = """
                INSERT INTO "game" ({})
                VALUES ({})
                RETURNING "game_id";
                """
        columns = ["\"game_name\"", "\"release_date\""]
        values = ["\'{}\'".format(game_name), "\'{}\'".format(release_date)]
        if price:
            columns.append("\"price\"")
            values.append(str(price))
        if total_achievements:
            columns.append("\"total_achievements\"")
            values.append(str(total_achievements))
        if positive_ratings:
            columns.append("\"positive_ratings\"")
            values.append(str(positive_ratings))
        if negative_ratings:
            columns.append("\"negative_ratings\"")
            values.append(str(negative_ratings))
        query = query.format(", ".join(columns), ", ".join(values))
        cursor.execute(query)
        game_id = cursor.fetchone()["game_id"]

        if genres:
            query = """
                    INSERT INTO "game_genre" ("game_id", "genre")
                    VALUES """
            values = []
            for genre in genres:
                values.append("({}, \'{}\')".format(game_id, genre))
            query += ", ".join(values) + ";"
            cursor.execute(query)
        
        else:
            query = """
                    INSERT INTO "game_genre" ("game_id", "genre")
                    VALUES ({}, 'Unknown')
                    """.format(game_id)
            cursor.execute(query)

        response = {
            "status": "OK",
            "gameID": game_id
        }

        sendall(client_sock, response)

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _admin_update_game(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_id = request["gameID"]
        genres = request.get("genres")
        price = request.get("price")
        total_achievements = request.get("totalAchievements")
        positive_ratings = request.get("positiveRatings")
        negative_ratings = request.get("negativeRatings")

        query = """
                SELECT COUNT(*)
                FROM "game"
                WHERE "game_id" = {};
                """.format(game_id)
        cursor.execute(query)
        game_found = cursor.fetchone()["count"]

        if game_found:
            query = """
                    UPDATE "game"
                    SET {{}}
                    WHERE "game_id" = {};
                    """.format(game_id)
            updates = []
            if price:
                updates.append("\"price\" = {}".format(price))
            if total_achievements:
                updates.append("\"total_achievements\" = {}".format(total_achievements))
            if positive_ratings:
                updates.append("\"positive_ratings\" = {}".format(positive_ratings))
            if negative_ratings:
                updates.append("\"negative_ratings\" = {}".format(negative_ratings))
            if updates:
                query = query.format(", ".join(updates))
                cursor.execute(query)

            if genres:
                query = """
                        DELETE FROM "game_genre"
                        WHERE "game_id" = {};
                        """.format(game_id)
                cursor.execute(query)

                query = """
                        INSERT INTO "game_genre" ("game_id", "genre")
                        VALUES """
                values = []
                for genre in genres:
                    values.append("({}, \'{}\')".format(game_id, genre))
                query += ", ".join(values) + ";"
                cursor.execute(query)

            response = {
                "status": "OK"
            }

        else:
            response = {
                "status": "FAIL",
                "errorMessage": "Game not found"
            }

        sendall(client_sock, response)

        pg_conn.commit()
    
    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _admin_delete_game(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        game_id = request["gameID"]

        query = """
                DELETE FROM "game"
                WHERE "game_id" = {};
                """.format(game_id)
        cursor.execute(query)

        response = {
            "status": "OK"
        }

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def _admin_setup_promotion(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket):
    try:
        start_date = request["startDate"]
        end_date = request["endDate"]
        discount_rate = request["discountRate"]

        query = """
                INSERT INTO "promotion" ("start_date", "end_date", "discount_rate")
                VALUES ('{}', '{}', {});
                """.format(start_date, end_date, discount_rate)
        cursor.execute(query)

        response = {
            "status": "OK"
        }

        sendall(client_sock, response)

        pg_conn.commit()

    except Exception as e:
        pg_conn.rollback()
        print("[Error] {}".format(e))
        response = {
            "status": "FAIL",
            "errorMessage": "Unknown error"
        }
        sendall(client_sock, response)

def handle_request(pg_conn: psycopg.Connection, request: dict, cursor: Cursor, client_sock: socket.socket) -> int:
    request_id = REQUEST_MAP[request["requestType"]]
    match request_id:
        case 0:
            _exit(pg_conn, request, cursor, client_sock)
            return RETCODE_EXIT
        case 1:
            _sign_in(pg_conn, request, cursor, client_sock)
        case 2:
            _sign_up(pg_conn, request, cursor, client_sock)
        case 3:
            _user_search_games(pg_conn, request, cursor, client_sock)
        case 4:
            _user_add_reviews(pg_conn, request, cursor, client_sock)
        case 5:
            _user_delete_reviews(pg_conn, request, cursor, client_sock)
        case 6:
            _user_add_to_favorites(pg_conn, request, cursor, client_sock)
        case 7:
            _user_create_room(pg_conn, request, cursor, client_sock)
        case 8:
            _user_join_room(pg_conn, request, cursor, client_sock)
        case 9:
            _user_check_user(pg_conn, request, cursor, client_sock)
        case 10:
            _user_update_profile(pg_conn, request, cursor, client_sock)
        case 11:
            _user_list_rooms(pg_conn, request, cursor, client_sock)
        case 12:
            _user_check_reviews(pg_conn, request, cursor, client_sock)
        case 13:
            _user_room_communication(pg_conn, request, cursor, client_sock)
        case 14:
            _user_leave_room(pg_conn, request, cursor, client_sock)
        case 15:
            _admin_add_game(pg_conn, request, cursor, client_sock)
        case 16:
            _admin_update_game(pg_conn, request, cursor, client_sock)
        case 17:
            _admin_delete_game(pg_conn, request, cursor, client_sock)
        case 18:
            _admin_setup_promotion(pg_conn, request, cursor, client_sock)
        case _:
           return RETCODE_ERROR

    return RETCODE_NORMAL    

def handle_client(client_sock: socket.socket, client_addr):
    try:
        pg_conn = psycopg.connect(
            host = PG_HOST,
            port = PG_PORT,
            user = PG_USER,
            password = PG_PASSWORD,
            dbname = PG_DBNAME
        )
        pg_conn.set_isolation_level(ISOLATION_LEVEL)
        cursor = pg_conn.cursor(row_factory = dict_row)
        while True:
            request_str = client_sock.recv(BUFFER_MAXLEN).decode("utf-8")
            if request_str:
                request = json.loads(request_str)
                retcode = handle_request(pg_conn, request, cursor, client_sock)
                if retcode == RETCODE_ERROR:
                    print("[Error] Failed to handle the request. Abort the client connection.")
                    break
                elif retcode == RETCODE_EXIT:
                    print("[Log] Client at {}:{} exited.".format(client_addr[0], client_addr[1]))
                    break

    finally:
        client_sock.close()
        cursor.close()
        pg_conn.close()
        exit(0)

def main(args):
    global PG_HOST
    global PG_PORT
    global PG_USER
    global PG_PASSWORD
    global PG_DBNAME

    PG_HOST = args.pg_host
    PG_PORT = args.pg_port
    PG_USER = args.pg_user
    PG_PASSWORD = args.pg_password
    PG_DBNAME = args.pg_dbname

    host = "127.0.0.1"
    port = args.port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)

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
        clear_screen()
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type = int, help = "The port for the server to listen on. (default = 8888)", default = 8888)
    parser.add_argument("--pg_host", type = str, help = "Host IP of the PostgreSQL server. (default = \"localhost\")", default = "localhost")
    parser.add_argument("--pg_port", type = int, help = "Port of the PostgreSQL server. (default = 5432)", default = 5432)
    parser.add_argument("--pg_user", type = str, help = "User to login PostgreSQL server. (default = \"postgres\")", default = "postgres")
    parser.add_argument("--pg_password", type = str, help = "Password for login the PostgreSQL server. (default = \"postgres\")", default = "postgres")
    parser.add_argument("--pg_dbname", type = str, help = "Database to connect. (default = \"Steam-Together\")", default = "Steam-Together")
    args = parser.parse_args()
    main(args)
