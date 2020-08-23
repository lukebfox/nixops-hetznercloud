from nixops.resources import ResourceOptions
from typing import Mapping


class HetznerCloudLoadBalancerOptions(ResourceOptions):
    apiToken: str
    labels: Mapping[str, str]
    location: str
    # networkId: str
    loadBalancerId: str
