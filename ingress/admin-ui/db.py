#!/usr/bin/python3

import os.path
import sys
import logging
import pickle
from werkzeug.security import generate_password_hash


class Singleton(object):
    _instance = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class Database(Singleton):
    open_tables = {}
    def __init__(self):
        self.db_prefix = "/data"

    def table(self, table_name: str, writable: bool = False):
        db_filename = os.path.join(self.db_prefix, table_name+".db")
        if db_filename not in self.open_tables:
            self.open_tables[db_filename] = Table(db_filename)
        return self.open_tables[db_filename]

class Table(object):
    def __init__(self, filename):
        self.filename = filename
        try:
            os.stat(filename)
        except FileNotFoundError:
            with open(filename, "wb") as file:
                pickle.dump({}, file)
        with open(filename, "rb") as file:
            self.data = pickle.load(file)
    def fetch(self, key):
        return self.data.get(key)
    def store(self, key, value):
        self.data.update({key: value})
    def items(self):
        return self.data.items()
    def keys(self):
        return self.data.keys()
    def exists(self, key):
        return key in self.data
    def drop(self, key):
        self.data.pop(key)
    def commit(self):
        with open(self.filename, "wb") as file:
            pickle.dump(self.data, file)




def setup_admin_table(username, password, lib_dir="/configs/"):
    db = Database()
    admins_table = db.table("admins", writable=True)
    admins_table.store(username, {
        "name": username,
        "password": generate_password_hash(password)
    })
    admins_table.commit()

    lib_table = db.table("lib", writable=True)
    with open(os.path.join(lib_dir, "ca.crt"), "r") as ca_file:
        lib_table.store("ca_cert", ca_file.read())
    lib_table.commit()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logging.fatal("No username or password provided")
    setup_admin_table(username=sys.argv[1], password=sys.argv[2])
