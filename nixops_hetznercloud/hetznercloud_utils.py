# -*- coding: utf-8 -*-

from hcloud import Client


def connect(api_token: str) -> Client:
    """
    Connect to the specified Hetzner Cloud API using the given token.
    """

    return Client(token=api_token)


def retry():
    """
    Retry function f up to 7 times.
    """
