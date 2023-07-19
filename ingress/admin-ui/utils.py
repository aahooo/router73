#!/usr/bin/python3

import re
import datetime
import arrow
import exceptions


def parse_time(timestr: str) -> arrow.Arrow:
    return arrow.get(timestr, "YYMMDDhhmmssZ")

def arrow_to_str(date: arrow.Arrow) -> str:
    return date.strftime("%y%m%d%H%M%SZ")

def datetime_to_str(date: datetime.datetime) -> str:
    return arrow_to_str(arrow.get(date))

def sanitize_name(name: str) -> str:
    invalid_client_pattern = "[^0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-]"
    if len(re.findall(invalid_client_pattern, name)) != 0:
        raise exceptions.InvalidUserName()
