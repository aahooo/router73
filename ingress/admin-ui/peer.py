#!/usr/bin/python3

from typing import Dict, List
import arrow

import db
import exceptions
import requests

CONFIG_TEMPLATE = """client
dev tun
proto tcp
remote #ADDR #PORT
resolv-retry infinite
nobind
persist-key
persist-tun
cipher AES-256-CBC
ignore-unknown-option block-outside-dns
auth-user-pass
verb 3
<ca>
#CA
</ca>
"""


class Peer(object):
    def __init__(self, name):
        table = db.Database().table("users", True)
        peer_data = table.fetch(name)
        if peer_data is None:
            raise exceptions.UserDoesNotExist(name)
        self.name = name
        self.password = peer_data.get("password")
        self.creation_date = arrow.get(peer_data["creation_date"])
        self.revokation_date = arrow.get(peer_data["revokation_date"])
        self.status = peer_data.get("status")

    def get_domain() -> str:
        response = requests.get('https://api.ipify.org')
        ip_address = response.text
        return ip_address


    def generate_config():
        config = CONFIG_TEMPLATE
        config = config.replace("#ADDR", Peer.get_domain())
        config = config.replace("#PORT", "444")
        config = config.replace("#CA", _get_ca_cert())
        return config


    def revoke_peer(self):
        table = db.Database().table("users", True)
        user_data = table.fetch(self.name)
        user_data["status"] = "revoked"
        table.store(self.name, user_data)
        table.commit()
        self.status = "revoked"

    def renew_peer(self):
        table = db.Database().table("users", True)
        user_data = table.fetch(self.name)
        user_data["status"] = "active"
        table.store(self.name, user_data)
        table.commit()
        self.status = "active"

    def get_info(self) -> Dict:
        return {"name": self.name, "password": self.password,
                "status": self.status, "creation": self.creation_date.for_json().split("T")[0]}

def _get_ca_cert() -> str:
    table = db.Database().table("lib")
    return table.fetch("ca_cert")
