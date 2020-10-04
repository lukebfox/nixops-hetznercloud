from nixops.backends import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional
from typing import Sequence


class ServerNetworkOptions(ResourceOptions):
    network: str
    privateIP: str
    aliasIPs: Sequence[str]


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
#    fileSystems: Optional[Mapping[str, FilesystemsOptions]]


class HetznerCloudMachineOptions(MachineOptions):
    hetznerCloud: HetznerCloudOptions
