#!/usr/bin/python3

from typing import Dict, List

import arrow

import exceptions
import utils
import db
from peer import Peer


def generate_peer(name: str, password: str) -> Peer:
    utils.sanitize_name(name)

    table = db.Database().table("users", True)
    if table.exists(name):
        raise exceptions.UserAlreadyExists(name)

    table.store(name, {
        "name": name,
        "password": password,
        "creation_date": arrow.now().datetime,
        "revokation_date": arrow.now().shift(months=1).datetime,
        "status": "active",
    })
    table.commit()

    return Peer(name)

def get_peers() -> List[str]:
    table = db.Database().table("users")
    peers = sorted([ peer[1]["name"] for peer in table.items() ])
    return peers


def get_active_peers() -> List[str]:
    table = db.Database().table("users")
    peers = sorted([ peer[1]["name"] for peer in table.items() if peer[1]["status"] == "active"])

    return [peer for peer in peers]


def get_revoked_peers() -> List[str]:
    table = db.Database().table("users")
    peers = sorted([ peer[1]["name"] for peer in table.items() if peer[1]["status"] != "active"])

    return [peer for peer in peers]


def get_admin_password_hash(username: str) -> Dict:
    table = db.Database().table("admins")
    try:
        return table.fetch(username).get("password")
    except:
        return None
