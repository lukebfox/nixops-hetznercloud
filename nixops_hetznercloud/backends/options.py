from nixops.backends import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional
from typing import Sequence


# class NetworkOptions(ResourceOptions):
#     networkId: str
#     privateIp: str
#     aliasIps: Optional[Sequence[str]]


class DiskOptions(ResourceOptions):
    volume: str
    mountPoint: Optional[str]
    # for automatically created resources
    size: int
    fsType: str
    deleteOnTermination: bool


class HetznerCloudOptions(ResourceOptions):
    apiToken: str
    location: str
    serverName: str
    serverType: str
    labels: Mapping[str, str]
    volumes: Sequence[DiskOptions]
    # serverNetworks: Sequence[NetworkOptions]
    # ipAddress: Optional[str]


class HetznerCloudMachineOptions(MachineOptions):
    hetznerCloud: HetznerCloudOptions
