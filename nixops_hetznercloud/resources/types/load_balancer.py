from nixops.resources import ResourceOptions
from typing import Mapping


class LoadBalancerOptions(ResourceOptions):
    apiToken: str
    labels: Mapping[str, str]
    location: str
