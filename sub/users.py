import json
import os
from time import time
from random import randint
import difflib
import discord
memory_dir = "\\".join([p for p in __file__.split("\\")[:-2]] + ["memory"])

def find_id_from_name(name) -> int | None:
    u = get_users()
    m = difflib.get_close_matches(str(name), [profile["name"] for profile in u.values()], n=1)
    if len(m) == 0:
        return None
    m = m[0]

    for user, profile in u.items():
        if profile["name"].lower() == m:
            return int(user)
    return None


def add_memory(user) -> int:
    raise NotImplementedError
    """
    Add a memory to a user's private memory by ID or name\n
    Returns:\n
    0: ok\n
    1: user not in users.json
    """
    i = True # if i then user is an ID
    for c in str(user):
        if c not in "1234567890":
            i = False
    
    if not i:
        user = find_id_from_name(user)
    
    if user == None:
        return 1

    private_memory_path = memory_dir + f"\\private\\{str(user)}.json"
    if not os.path.exists(private_memory_path):
        with open(private_memory_path, "x") as memories:
            json.dump({
                "name":get_user(user)["name"],
                "memories":{}
            }, memories)
            
def get_user(id) -> dict[str, str] | None:
    """
    Get a user's name and description from users.json\n
    If user exists: returns dict[str, str] {"name": name, "desc": desc}
    If user does not exist: returns None
    """
    i = True # true if id is a number, if false its probably a name
    for c in str(id):
        if c not in "1234567890":
            i = False
    
    if not i:
        id = find_id_from_name(id.lower())
    
    if id == None:
        return None

    with open(memory_dir + "\\users.json", "r") as users_file:
        users_json = json.load(users_file)

    if str(id) in users_json["users"]:
        r = users_json["users"][str(id)]
        r["id"] = id
        return r
    else:
        return None
    
def get_users() -> dict[str, dict[str, str]]:
    """
    Returns every user in users.json with name and desc
    """
    with open(memory_dir + "\\users.json", "r") as users_file:
        users_json = json.load(users_file)
    
    return users_json["users"]

def update_user(id, name: str | None, desc: str | None) -> None:
    """
    Update a user's entry in the users.json file\n
    If user doesn't exist, add them
    """
    with open(memory_dir + "\\users.json", "r") as users_file:
        users_json = json.load(users_file)
    
    users_json["last_update"] = time()
    if str(id) not in users_json["users"].keys():
        users_json["users"][str(id)] = {"name": f"unknown {str(id)}", "desc": "no description"}
    old = users_json["users"][str(id)]

    new = {"name": old["name"], "desc": old["desc"]}
    if name != None:
        new["name"] = name
    if desc != None:
        new["desc"] = old["desc"] + "\n" + desc
    
    users_json["users"][str(id)] = new

    with open(memory_dir + "\\users.json", "w") as users_file:
        json.dump(users_json, users_file)

def clear_users() -> None:
    """
    Clear all user descriptions from users.json (authentication required)
    """
    conf = f"{randint(0, 999999):6.0f}"
    if input(f"CLEAR_USERS() CALLED\nCLEAR USERS? ENTER CONFIRMATION {conf} TO CONFIRM\n> ") != conf:
        print("INCORRECT")
    else:
        print("CORRECT")

    with open(memory_dir + "\\users.json", "r") as users_file:
        users_json = json.load(users_file)
    
    users_json["last_update"] = time()
    users_json["users"] = {}

    with open(memory_dir + "\\users.json", "w") as users_file:
        json.dump(users_json, users_file)
    
    update_user("1373241417211838474", "jarvis", "you")