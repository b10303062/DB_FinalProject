import sys
import argparse
import socket
import shutil
import getpass
import json
import select
import datetime
from display_utils import *
from network_utils import *

RETCODE_NORMAL = 1
RETCODE_QUIT = 0
RETCODE_ERROR = -1
BUFFER_MAXLEN = 8192

PAGE_STACK_MAXLEN = 10

# General page header
PAGE_HEADER = \
"""{0:=^{width}}\n
{1}{{: ^{width}}}{2}\n
{3:=^{width}}
""".format("", STYLE_BOLD, STYLE_DEFAULT, "", width = shutil.get_terminal_size()[0])

# Pre-defined pages
PAGE_INITIALIZE = \
"""{}
How can we help you?

[1] Sign in

[2] Sign up

[q] Quit
""".format(PAGE_HEADER.format("Steam-Together"))

PAGE_SIGN_IN = \
"""{}""".format(PAGE_HEADER.format("Sign In"))

PAGE_SIGN_UP = \
"""{}""".format(PAGE_HEADER.format("Sign Up"))

PAGE_USER_DASHBOARD = \
"""{}
Please choose from the below options:

[1] Search games

[2] Add/Delete reviews

[3] Add games to my favorites

[4] Create a room

[5] Join a room

[6] Check user information 

[7] Update my profile

[8] List active rooms

[9] Check game reviews

[c] Clear the screen

[q] Quit
""".format(PAGE_HEADER.format("User Dashboard"))

PAGE_ROOM = \
"""{}""".format(PAGE_HEADER.format("ROOM"))

PAGE_ADMIN = \
"""{}
Please choose from the below options:

[1] Add game

[2] Update game

[3] Search game

[4] Delete game

[5] Update user

[c] Clear the screen

[q] Quit
""".format(PAGE_HEADER.format("Admin Dashboard"))

PAGETYPE_INITIALIZE = 1
PAGETYPE_SIGN_IN = 2
PAGETYPE_SIGN_UP = 3
PAGETYPE_USER_DASHBOARD = 4
PAGETYPE_ROOM = 5
PAGETYPE_ADMIN = 6

# Record info for login user
user_state = {
    "userID": -1,
    "userName": "",
    "room": {
        "roomID": -1,
        "roomName": "",
        "roomHost": "",
        "roomNumMembers": -1,
        "roomNumMembersLimit": -1
    }
}

def _init_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    while True:
        command_prompt()
        opt = input()
        if opt == "1":
            pages.append((PAGETYPE_SIGN_IN, PAGE_SIGN_IN))
            return RETCODE_NORMAL
        elif opt == "2":
            pages.append((PAGETYPE_SIGN_UP, PAGE_SIGN_UP))
            return RETCODE_NORMAL
        elif opt == "q":
            request = {
                "requestType": "exit",
                "userID": user_state["userID"]
            }
            sendall(server_sock, request)
            return RETCODE_QUIT
        else:
            print("Invalid option id. Please enter again.")

def _sign_in_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    while True:
        user_id = input("User ID: ")
        try:
            user_id = int(user_id)
            break
        except:
            print("Invalid input. Please try again.")
    password = getpass.getpass(prompt = "Password: ")
    request = {
        "requestType": "sign in",
        "userID": user_id,
        "password": password
    }
    sendall(server_sock, request)
    response = json.loads(recvall(server_sock, BUFFER_MAXLEN))
    if response["status"] == "OK":
        user_state["userID"] = user_id
        user_state["userName"] = response["userName"]
        print("Sign in ok.")
        press_enter_to_continue()
        if response["role"] == "User":
            pages.append((PAGETYPE_USER_DASHBOARD, PAGE_USER_DASHBOARD))
            return RETCODE_NORMAL
        elif response["role"] == "Business Operator":
            pages.append((PAGETYPE_ADMIN, PAGE_ADMIN))
            return RETCODE_NORMAL
        else:
            return RETCODE_ERROR
    elif response["status"] == "FAIL":
        print("Sign in failed. Get the following error from the server: {}".format(response["errorMessage"]))
        press_enter_to_continue()
        pages.append((PAGETYPE_INITIALIZE, PAGE_INITIALIZE))
        return RETCODE_NORMAL
    else:
        return RETCODE_ERROR
        
def _sign_up_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    user_name = input("User name: ")
    email = input("Email: ")
    while True:
        role = input("Role (User or Business Operator): ")
        if role == "User" or role == "Business Operator":
            break
        else:
            print("Invalid input. Please try again.")
    while True:
        password = getpass.getpass(prompt = "Password: ")
        password_check = getpass.getpass(prompt = "Password again: ")
        if password == password_check:
            break
        else:
            print("Your second input for password is different from the first one. Please try again.")

    request = {
        "requestType": "sign up",
        "userName": user_name,
        "email": email,
        "password": password,
        "role": role
    }
    sendall(server_sock, request)
    response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

    if response["status"] == "OK":
        print("Sign up OK.")
        print("Your user id is {}. Please remember it since you need it to sign in.".format(FG_COLOR_GREEN + str(response["userID"]) + STYLE_DEFAULT))
        press_enter_to_continue()
        pages.append((PAGETYPE_INITIALIZE, PAGE_INITIALIZE))
        return RETCODE_NORMAL
    
    elif response["status"] == "FAIL":
        print("Sign up failed. Get the following error from server: {}".format(response["errorMessage"]))
        press_enter_to_continue()
        pages.append((PAGETYPE_INITIALIZE, PAGE_INITIALIZE))
        return RETCODE_NORMAL
    
    else:
        return RETCODE_ERROR

def _user_dashboard_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    while True:
        command_prompt(user_state["userName"])
        opt = input()
        match opt:
            case "1": # Search games
                game_name = input("Game name (Press ENTER if you want to skip this): ")
                if game_name == "":
                    game_name = None
                genres = input("Game genres (Press ENTER if you want to skip this. Split by commas if multiple inputs): ")
                genres = [genre.strip() for genre in genres.split(",")] if genres else None
                while True:
                    price_low = input("Price lower bound (Press ENTER if you want to skip this): ")
                    if not price_low:
                        price_low = None
                        break
                    else:
                        try:
                            price_low = float(price_low)
                            break
                        except:
                            print("Invalid input. Please try again.")
                            continue
                while True:
                    price_upp = input("Price upper bound (Press ENTER if you want to skip this): ")
                    if not price_upp:
                        price_upp = None
                        break
                    else:
                        try:
                            price_upp = float(price_upp)
                            break
                        except:
                            print("Invalid input. Please try again.")

                request = {
                    "requestType": "search games",
                    "gameName": game_name,
                    "genres": genres,
                    "priceLow": price_low,
                    "priceUpp": price_upp
                }
                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Results:\n")
                    if game_name:
                        game_name_lc = game_name.lower()
                    for data in response["data"]:
                        if game_name:
                            match_pos = data["gameName"].lower().find(game_name_lc)
                            game_name_formatted = "{}{}{}{}{}".format(
                                data["gameName"][:match_pos],
                                FG_COLOR_GREEN,
                                data["gameName"][match_pos:match_pos + len(game_name)],
                                STYLE_DEFAULT,
                                data["gameName"][match_pos + len(game_name):]
                            )
                            print("Game:\t\t\t{}".format(game_name_formatted))
                        else:
                            print("Game:\t\t\t{}".format(data["gameName"]))
                        print("Game ID:\t\t{}".format(data["gameID"]))
                        print("Genres:\t\t\t{}".format("/".join(data["genres"])))
                        print("Release Date:\t\t{}".format(data["releaseDate"]))
                        print("Total Achievements:\t{}".format(data["totalAchievements"]))
                        print("Positive Ratings:\t{}".format(data["positiveRatings"]))
                        print("Negative Ratings:\t{}".format(data["negativeRatings"]))
                        print()

                    print("{} games were found.".format(len(response["data"])))
                    press_enter_to_continue()

                    return RETCODE_NORMAL

                elif response["status"] == "FAIL":
                    print("Get the following error from server: {}".format(response))              
                    return RETCODE_NORMAL
                
                else:
                    return RETCODE_ERROR

            case "2": # Add/Delete Reviews
                options_prompt = "What do you want to do with your review? [A]add [D]delete"
                print(options_prompt)

                while True:
                    opt = input("your option: ")
                    if opt == "A" or opt == "D":
                        break
                    else:
                        print("Invalid input. Please try again.")

                if opt == "A":
                    while True:
                        try:
                            game_id = int(input("game id: "))
                            break
                        except:
                            print("Invalid input. Please try again.")
                    review_text = input("Please write your review (Or press ENTER to skip): ")
                    while True:
                        try:
                            review_rating = int(input("Please rate this game (select an integer from 1 to 5): "))
                            break
                        except:
                            print("Invalid input. Please try again.")

                    request = {
                        "requestType": "add review",
                        "userID": user_state["userID"],
                        "gameID": game_id,
                        "reviewText": review_text,
                        "reviewRating": review_rating
                    }
                else:
                    while True:
                        try:
                            game_id = int(input("game id: "))
                            break
                        except:
                            print("Invalid input. Please try again.")

                    request = {
                        "requestType": "delete review",
                        "userID": user_state["userID"],
                        "gameID": game_id
                    }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    if opt == "A":
                        print("Your review on the game is recorded.")

                        if response.get("recommendations"):
                            print("\nWe recommend the following games for you:\n")
                            for rec in response["recommendations"]:
                                print("Game Name: {}".format(rec["gameName"]))
                                print("Game ID: {}".format(rec["gameID"]))
                                print("Positive Ratings: {}".format(rec["positiveRatings"]))
                                print()
                        
                        press_enter_to_continue()
                    else:
                        print("Your review on the game is deleted.")
                        press_enter_to_continue()
                elif response["status"] == "FAIL":
                    print("Operation failed. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                else:
                    return RETCODE_ERROR

                return RETCODE_NORMAL
            
            case "3": # Add to favorites
                while True:
                    try:
                        game_id = int(input("Please input the game id: "))
                        break                    
                    except:
                        print("Invalid input, Please try again.")
                request = {
                    "requestType": "add to favorite",
                    "userID": user_state["userID"],
                    "gameID": game_id
                }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("The game has been add to your favorites.")
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to update favorites. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "4": # Create a room
                room_name = input("The name of your room: ")
                while True:
                    try:
                        game_id = int(input("Determine the game you want to play and input the game id: "))
                        break
                    except:
                        print("Invalid input. Please try again.")
                while True:
                    max_members = input("Determine the maximum members for the room (Press ENTER if you want to skip this. Default is 10): ")
                    if max_members:
                        try:
                            max_members = int(max_members)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        max_members = 10
                        break
                request = {
                    "requestType": "create room",
                    "userID": user_state["userID"],
                    "roomName": room_name,
                    "roomNumMembersLimit": max_members,
                    "gameID": game_id
                }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    room_id = response["roomID"]
                    game_name = response["gameName"]
                    user_state["room"]["roomID"] = room_id
                    user_state["room"]["roomName"] = room_name
                    user_state["room"]["roomHost"] = user_state["userName"]
                    user_state["room"]["roomNumMembers"] = 1
                    user_state["room"]["roomNumMembersLimit"] = max_members
                    room_page = \
"""{:=^{width}}
{}{: ^{width}}{}
{: ^{width}}
{:=^{width}}
{: ^{width}}
{:=^{width}}
{: ^{width}}
{:=^{width}}
""".format("", STYLE_BOLD, room_name, STYLE_DEFAULT, "ID: {}".format(room_id), "", "Play Game: {}".format(game_name), "", "Host: {}".format(user_state["room"]["roomHost"]), "", width = shutil.get_terminal_size()[0])
                    pages.append((PAGETYPE_ROOM, room_page))
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to create a room. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "5": # Join a room
                while True:
                    room_id = input("Please enter the id of the room to join: ")
                    try:
                        room_id = int(room_id)
                        break
                    except:
                        print("Invalid input. Please try again.")
                
                request = {
                    "requestType": "join room",
                    "userID": user_state["userID"],
                    "roomID": room_id
                }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    user_state["room"]["roomID"] = room_id
                    room_name = response["roomName"]
                    room_host = response["roomHost"]
                    game_name = response["gameName"]
                    user_state["room"]["roomNumMembers"] = response["roomNumMembers"]
                    user_state["room"]["roomNumMembersLimit"] = response["roomNumMembersLimit"]
                    user_state["room"]["roomName"] = room_name
                    user_state["room"]["roomHost"] = room_host
                    room_page = \
"""{:=^{width}}
{}{: ^{width}}{}
{: ^{width}}
{:=^{width}}
{: ^{width}}
{:=^{width}}
{: ^{width}}
{:=^{width}}
""".format("", STYLE_BOLD, room_name, STYLE_DEFAULT, "ID: {}".format(room_id), "", "Play Game: {}".format(game_name), "", "Host: {}".format(user_state["room"]["roomHost"]), "", width = shutil.get_terminal_size()[0])
                    pages.append((PAGETYPE_ROOM, room_page))
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to join the room. Get the following message from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "6": # Check user information
                while True:
                    try:
                        user_id = int(input("Please input the id of the target user: "))
                        break
                    except:
                        print("Invalid input. Please try again.")
                request = {
                    "requestType": "check user",
                    "userID": user_id
                }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Found user:\n")
                    print("User ID:   {}".format(response["userInfo"]["id"]))
                    print("User Name: {}".format(response["userInfo"]["name"]))
                    print("Join Date: {}".format(response["userInfo"]["joinDate"]))
                    print("Favorites:")
                    for fav in response["userInfo"]["favorites"]:
                        print("    Game ID:   {}".format(fav["gameID"]))
                        print("    Game Name: {}".format(fav["gameName"]))
                        print()
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to get user information. Get the following error from server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "7": # Update profile
                print("Please enter the new information. You can press ENTER to skip if you're not going to update that information.")
                new_name = input("Name: ")
                new_email = input("Email: ")
                while True:
                    new_password = getpass.getpass("New Password: ")
                    if new_password:
                        new_password_check = getpass.getpass("Please enter the new password again: ")
                        if new_password == new_password_check:
                            break
                        else:
                            print("The second password is differ from the first one. Please try again.")
                    else:
                        break

                request = {
                    "requestType": "update profile",
                    "userID": user_state["userID"],
                    "updated": {}
                }
                if new_name:
                    request["updated"]["name"] = new_name
                if new_email:
                    request["updated"]["email"] = new_email
                if new_password:
                    request["updated"]["password"] = new_password

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Update OK. The updated profile is listed below:")
                    print("Name:\t{}".format(response["userProfile"]["name"]))
                    print("Email:\t{}".format(response["userProfile"]["email"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Update failed. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "8": # List active rooms
                while True:
                    game_id = input("Input id of the game that you want to play (Press ENTER if you want to skip this): ")
                    if game_id:
                        try:
                            game_id = int(game_id)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        break

                request = {
                    "requestType": "list rooms",
                    "gameID": game_id
                }
                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Results:\n")
                    for room in response["rooms"]:
                        print("Room Name: {}".format(room["roomName"]))
                        print("Room ID: {}".format(room["roomID"]))
                        print("Play Game: {}".format(room["playGame"]))
                        print("Host ID: {}".format(room["hostID"]))
                        print("Host Name: {}".format(room["hostName"]))
                        print("Num Members: {:2d}/{:2d}".format(room["roomNumMembers"], room["roomNumMembersLimit"]))
                        print()
                    print("{} rooms has been found.".format(len(response["rooms"])))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to search rooms. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "9": # Check user reviews
                while True:
                    try:
                        game_id = int(input("Please enter the game id: "))
                        break
                    except:
                        print("Invalid input. Please try again.")
                while True:
                    user_id = input("Please input the id of the target user (Press ENTER if you want to skip this): ")
                    if user_id:
                        try:
                            user_id = int(user_id)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        break
                while True:
                    rating = input("Please input the target rating number (Press ENTER if you want to skip this): ")
                    if rating:
                        try:
                            rating = int(rating)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        break
                
                request = {
                    "requestType": "check reviews",
                    "gameID": game_id
                }
                if user_id:
                    request["userID"] = user_id
                if rating:
                    request["rating"] = rating

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Results:\n")
                    for review in response["reviews"]:
                        print("User ID: {}".format(review["userID"]))
                        print("Review: {}".format(review["reviewText"]))
                        print("Rating: {}".format(review["reviewRating"]))
                        print()
                    print("{} reviews were found.".format(len(response["reviews"])))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to get review. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR

            case "c":
                return RETCODE_NORMAL

            case "q":
                request = {
                    "requestType": "exit",
                    "userID": user_state["userID"]
                }
                server_sock.send(json.dumps(request).encode('utf-8'))
                return RETCODE_QUIT
            
            case _:
                print("Invalid option id. Please try again.")

def json_split(json_stream: str):
    jsons = []
    stack_len = 0
    init = True
    start = 0
    end = 0
    for i in range(len(json_stream)):
        if json_stream[i] == "{":
            init = False
            stack_len += 1
        elif json_stream[i] == "}":
            stack_len -= 1
        
        if stack_len == 0 and not init:
            start = end
            end = i + 1
            jsons.append(json_stream[start:end])

    return jsons
    
def _room_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    messages = []
    rlist = [sys.stdin, server_sock]
    leave = False
    close = False
    n_members = user_state["room"]["roomNumMembers"]
    n_members_max = user_state["room"]["roomNumMembersLimit"]
    while not leave and not close:
        clear_screen()
        print(pages[-1][1], end = "")
        print("{: ^{width}}\n{:=^{width}}".format("Members: {:2d}/{:2d}".format(n_members, n_members_max), "", width = shutil.get_terminal_size()[0]))
        for msg in messages:
            if msg[0] == user_state["userID"]:
                print(STYLE_BOLD + "[{}] {}".format(msg[1], msg[2]) + STYLE_DEFAULT)
            elif msg[0] > 0:
                print("[{}] {}".format(msg[1], msg[2]))
            else:
                print(FG_COLOR_YELLOW + msg[2] + STYLE_DEFAULT)
        print("\033[{};1HMessage > \033[0m".format(shutil.get_terminal_size()[1]), flush = True, end = "")

        readables, _, _ = select.select(rlist, [], [])

        for readable in readables:
            if readable == sys.stdin:
                line = sys.stdin.readline().strip('\n')
                if line:
                    if line == "\\quit":
                        leave = True
                    else:
                        request = {
                            "requestType": "room communication",
                            "roomID": user_state["room"]["roomID"],
                            "fromUserID": user_state["userID"],
                            "timestamp": str(datetime.datetime.now().replace(microsecond=0)),
                            "content": line
                        }
                        sendall(server_sock, request)
                        response = json.loads(recvall(server_sock, BUFFER_MAXLEN))
                        if response["status"] == "OK":
                            messages.append((user_state["userID"], user_state["userName"], line))
            elif readable == server_sock:
                server_message = json.loads(recvall(server_sock, BUFFER_MAXLEN))
                if server_message:
                    if server_message["messageType"] == "room communication":    
                        messages.append((server_message["fromUserID"], server_message["fromUserName"], server_message["content"]))
                    elif server_message["messageType"] == "room control":
                        if server_message["event"] == "join":
                            n_members += 1
                            messages.append((-1, "", "{} joined the room.".format(server_message["userName"])))
                        elif server_message["event"] == "leave":
                            n_members -= 1
                            messages.append((-1, "", "{} left the room.".format(server_message["userName"])))
                        elif server_message["event"] == "close":
                            close = True
                        else:
                            return RETCODE_ERROR
    
    # leave room
    if leave:
        request = {
            "requestType": "leave room",
            "userID": user_state["userID"],
            "roomID": user_state["room"]["roomID"]
        }
        sendall(server_sock, request)
        response = json.loads(recvall(server_sock, BUFFER_MAXLEN))
        if response["status"] == "OK":
            print("\033[{};1HYou will now leave the room.\033[0m".format(shutil.get_terminal_size()[1]))
    print("\033[{};1HThe room will be closed as the host has exited.\033[0m".format(shutil.get_terminal_size()[1]))
    press_enter_to_continue()
    pages.append((PAGETYPE_USER_DASHBOARD, PAGE_USER_DASHBOARD))
    return RETCODE_NORMAL

def _admin_page(server_sock: socket.socket, pages: list[tuple]) -> int:
    while True:
        command_prompt(user_state["userName"])
        opt = input()
        match opt:
            case "1":
                game_name = input("Game name: ")
                while True:
                    release_date = input("Release date in format YYYY-MM-DD: ")
                    try:
                        datetime.date.fromisoformat(release_date)
                        break
                    except Exception as e:
                        print("Invalid input. Please try again.")
                        print(FG_COLOR_YELLOW + "Hint: {}".format(e) + STYLE_DEFAULT)
                genres = input("Game genres (Press ENTER if you want to skip this. Split by commas if multiple inputs): ")
                genres = [genre.strip() for genre in genres.split(',')] if genres else None
                while True:
                    price = input("Price (Press ENTER if you want to skip this): ")
                    if price:
                        try:
                            price = float(price)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        price = None
                        break
                while True:
                    total_achievements = input("Total achievements in the game (Press ENTER if you want to skip this): ")
                    if total_achievements:
                        try:
                            total_achievements = int(total_achievements)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        total_achievements = None
                        break
                while True:
                    positive_ratings = input("Number of positive ratings (Press ENTER if you want to skip this): ")
                    if positive_ratings:
                        try:
                            positive_ratings = float(positive_ratings)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        positive_ratings = None
                        break
                while True:
                    negative_ratings = input("Number of negative ratings (Press ENTER if you want to skip this): ")
                    if negative_ratings:
                        try:
                            negative_ratings = float(negative_ratings)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        negative_ratings = None
                        break

                request = {
                    "requestType": "add game",
                    "gameName": game_name,
                    "genres": [],
                    "releaseDate": release_date,
                    "price": price,
                    "totalAchievements": total_achievements,
                    "positiveRatings": positive_ratings,
                    "negativeRatings": negative_ratings
                }
                if genres:
                    for genre in genres:
                        request["genres"].append(genre)
                
                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("The game has been added to the database.")
                    print("The game id is {}. Please remember it for further operations.".format(FG_COLOR_GREEN + str(response["gameID"]) + STYLE_DEFAULT))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to add the game into database. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR
            
            case "2":
                while True:
                    game_id = input("Game id: ")
                    try:
                        game_id = int(game_id)
                        break
                    except:
                        print("Invalid input. Please try again.")
                genres = input("Game genres (Press ENTER if you want to skip this. Split by commas if multiple inputs): ")
                genres = [genre.strip() for genre in genres.split(',')] if genres else None
                while True:
                    price = input("Price (Press ENTER if you want to skip this): ")
                    if price:
                        try:
                            price = float(price)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        price = None
                        break
                while True:
                    total_achievements = input("Total achievements in the game (Press ENTER if you want to skip this): ")
                    if total_achievements:
                        try:
                            total_achievements = int(total_achievements)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        total_achievements = None
                        break
                while True:
                    positive_ratings = input("Number of positive ratings (Press ENTER if you want to skip this): ")
                    if positive_ratings:
                        try:
                            positive_ratings = float(positive_ratings)
                            break
                        except:
                            print("Invalid input. Please try again.")
                    else:
                        positive_ratings = None
                        break
                while True:
                    negative_ratings = input("Number of negative ratings (Press ENTER if you want to skip this): ")
                    if negative_ratings:
                        try:
                            negative_ratings = float(negative_ratings)
                            break
                        except:
                            print("Invalud input. Please try again.")
                    else:
                        negative_ratings = None
                        break

                request = {
                    "requestType": "update game",
                    "gameID": game_id,
                    "genres": [],
                    "price": price,
                    "totalAchievements": total_achievements,
                    "positiveRatings": positive_ratings,
                    "negativeRatings": negative_ratings
                }
                if genres:
                    for genre in genres:
                        request["genres"].append(genre)
                
                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("The game has been updated.")
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to update the game. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR
            
            case "3":
                game_name = input("Game name (Press ENTER if you want to skip this): ")
                if game_name == "":
                    game_name = None
                genres = input("Game genres (Press ENTER if you want to skip this. Split by commas if multiple inputs): ")
                genres = [genre.strip() for genre in genres.split(",")] if genres else None
                while True:
                    price_low = input("Price lower bound (Press ENTER if you want to skip this): ")
                    if not price_low:
                        price_low = None
                        break
                    else:
                        try:
                            price_low = float(price_low)
                            break
                        except:
                            print("Invalid input. Please try again.")
                            continue
                while True:
                    price_upp = input("Price upper bound (Press ENTER if you want to skip this): ")
                    if not price_upp:
                        price_upp = None
                        break
                    else:
                        try:
                            price_upp = float(price_upp)
                            break
                        except:
                            print("Invalid input. Please try again.")

                request = {
                    "requestType": "search games",
                    "gameName": game_name,
                    "genres": genres,
                    "priceLow": price_low,
                    "priceUpp": price_upp
                }
                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Results:\n")
                    if game_name:
                        game_name_lc = game_name.lower()
                    for data in response["data"]:
                        if game_name:
                            match_pos = data["gameName"].lower().find(game_name_lc)
                            game_name_formatted = "{}{}{}{}{}".format(
                                data["gameName"][:match_pos],
                                FG_COLOR_GREEN,
                                data["gameName"][match_pos:match_pos + len(game_name)],
                                STYLE_DEFAULT,
                                data["gameName"][match_pos + len(game_name):]
                            )
                            print("Game:\t\t\t{}".format(game_name_formatted))
                        else:
                            print("Game:\t\t\t{}".format(data["gameName"]))
                        print("Game ID:\t\t{}".format(data["gameID"]))
                        print("Genres:\t\t\t{}".format("/".join(data["genres"])))
                        print("Release Date:\t\t{}".format(data["releaseDate"]))
                        print("Total Achievements:\t{}".format(data["totalAchievements"]))
                        print("Positive Ratings:\t{}".format(data["positiveRatings"]))
                        print("Negative Ratings:\t{}".format(data["negativeRatings"]))
                        print()

                    print("{} games were found.".format(len(response["data"])))
                    press_enter_to_continue()

                    return RETCODE_NORMAL

                elif response["status"] == "FAIL":
                    print("Get the following error from server: {}".format(response))              
                    return RETCODE_NORMAL
                
                else:
                    return RETCODE_ERROR                

            case "4":
                while True:
                    game_id = input("Game id: ")
                    try:
                        game_id = int(game_id)
                        break
                    except:
                        print("Invalid input. Please try again.")
                request = {
                    "requestType": "delete game",
                    "gameID": game_id
                }

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("The game has deleted.")
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Failed to delete the game. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR
            
            case "5":
                print("Please enter the new information. You can press ENTER to skip if you're not going to update that information.")
                while True:
                    user_id = input("User id: ")
                    try:
                        user_id = int(user_id)
                        break
                    except:
                        print("Invalid input. Please try again.")
                new_name = input("Name: ")
                new_email = input("Email: ")
                while True:
                    new_password = getpass.getpass("New Password: ")
                    if new_password:
                        new_password_check = getpass.getpass("Please enter the new password again: ")
                        if new_password == new_password_check:
                            break
                        else:
                            print("The second password differs from the first one. Please try again.")
                    else:
                        break

                request = {
                    "requestType": "update profile",
                    "userID": user_id,
                    "updated": {}
                }
                if new_name:
                    request["updated"]["name"] = new_name
                if new_email:
                    request["updated"]["email"] = new_email
                if new_password:
                    request["updated"]["password"] = new_password

                sendall(server_sock, request)
                response = json.loads(recvall(server_sock, BUFFER_MAXLEN))

                if response["status"] == "OK":
                    print("Update OK. The updated profile is listed below:")
                    print("Name:\t{}".format(response["userProfile"]["name"]))
                    print("Email:\t{}".format(response["userProfile"]["email"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                elif response["status"] == "FAIL":
                    print("Update failed. Get the following error from the server: {}".format(response["errorMessage"]))
                    press_enter_to_continue()
                    return RETCODE_NORMAL
                else:
                    return RETCODE_ERROR
            
            case "c":
                return RETCODE_NORMAL
            
            case "q":
                request = {
                    "requestType": "exit",
                    "userID": user_state["userID"]
                }
                server_sock.send(json.dumps(request).encode('utf-8'))
                return RETCODE_QUIT
            case _:
                print("Invalid option. Please try again.")

def page_handle(server_sock: socket.socket, pages: list[tuple]) -> int:
    page_type = pages[-1][0]
    if page_type == PAGETYPE_INITIALIZE:
        return _init_page(server_sock, pages)
    elif page_type == PAGETYPE_SIGN_IN :
        return _sign_in_page(server_sock, pages)
    elif page_type == PAGETYPE_SIGN_UP:
        return _sign_up_page(server_sock, pages)
    elif page_type == PAGETYPE_USER_DASHBOARD:
        return _user_dashboard_page(server_sock, pages)
    elif page_type == PAGETYPE_ROOM:
        return _room_page(server_sock, pages)
    elif page_type == PAGETYPE_ADMIN:
        return _admin_page(server_sock, pages)
    else:
        return RETCODE_ERROR

def main(args):
    host = args.host
    port = args.port

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_sock.connect((host, port))

        print("Connect to server {}:{}".format(host, port))
        press_enter_to_continue()
        clear_screen()

        pages = [(PAGETYPE_INITIALIZE, PAGE_INITIALIZE)]
        while True:
            clear_screen()
            print(pages[-1][1], end = "")

            code = page_handle(server_sock, pages)
            if code == RETCODE_ERROR:
                server_sock.close()
                raise Exception("Detect unexpected error. Aborted.\n")
            elif code == RETCODE_QUIT:
                break

            if len(pages) > PAGE_STACK_MAXLEN:
                pages = pages[-PAGE_STACK_MAXLEN:]

    finally:
        server_sock.close()
        clear_screen()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", type = str, help = "Server's host address.", default = "127.0.0.1")
    parser.add_argument("-p", "--port", type = int, help = "Server's port.", default = 8888)
    args = parser.parse_args()
    main(args)