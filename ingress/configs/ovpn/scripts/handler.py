#!/usr/bin/python3
import os, sys
import requests



def auth_user_pass():
    username = os.environ["username"]
    password = os.environ["password"]

    req = requests.post("http://admin-ui:80/check-password", json={"peer": username, "password": password})
    if req.status_code != 200 or req.text != "success":
        return 1

    # TODO make this a dns name
    req = requests.get("http://admin-ui:80/peer-status?peer="+username)
    if req.status_code != 200 or req.text != "active":
        return 1
    
    return 0

if __name__ == "__main__":
    script_type = os.environ["script_type"]
    if script_type == "user-pass-verify":
        auth_user_pass()
    else:
        print(f"type is `{script_type}`")
        sys.exit(1)
