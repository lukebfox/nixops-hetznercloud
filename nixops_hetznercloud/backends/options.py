from nixops.backends import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping, Optional, Sequence


class ServerNetworkOptions(ResourceOptions):
    network: str
    privateIpAddress: str
    aliasIpAddresses: Sequence[str]


class DiskOptions(ResourceOptions):
    volume: str
    size: int
    fsType: str
    mountPoint: Optional[str]


class HetznerCloudOptions(ResourceOptions):
    apiToken: str
    location: str
    serverName: str
    serverType: str
    labels: Mapping[str, str]
    volumes: Sequence[DiskOptions]
    ipAddresses: Sequence[str]
    serverNetworks: Sequence[ServerNetworkOptions]


class HetznerCloudMachineOptions(MachineOptions):
    hetznerCloud: HetznerCloudOptions
