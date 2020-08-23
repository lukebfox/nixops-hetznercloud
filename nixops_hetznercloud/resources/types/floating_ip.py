from nixops.resources import ResourceOptions
from typing import Mapping


class HetznerCloudFloatingIPOptions(ResourceOptions):
    apiToken: str
    description: str
    type: str
    location: str
    labels: Mapping[str, str]
    floatingIpId: str
    address: str
