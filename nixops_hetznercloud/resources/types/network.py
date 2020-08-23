from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Sequence


class HetznerCloudRouteOptions(ResourceOptions):
    destination: str
    gateway: str


class HetznerCloudNetworkOptions(ResourceOptions):
    apiToken: str
    ipRange: str
    subnets: Sequence[str]
    routes: Sequence[HetznerCloudRouteOptions]
    labels: Mapping[str, str]
    networkId: str
