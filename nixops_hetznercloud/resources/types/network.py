from nixops.resources import ResourceOptions
from typing import Mapping, Sequence


class RouteOptions(ResourceOptions):
    destination: str
    gateway: str


class NetworkOptions(ResourceOptions):
    apiToken: str
    ipRange: str
    subnets: Sequence[str]
    routes: Sequence[RouteOptions]
    labels: Mapping[str, str]
