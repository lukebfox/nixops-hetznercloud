# -*- coding: utf-8 -*-

import hcloud

def connect(api_token: str) -> Client:
    return hcloud.Client(token=api_token)
