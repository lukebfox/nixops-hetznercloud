from nixops.backends import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional

# from typing import Sequence


# class NetworkOptions(ResourceOptions):
#    networkId: str
#    privateIp: str
#    aliasIps: Optional[Sequence[str]]


class DiskOptions(ResourceOptions):
   volume: str
#   size: int
#   fsType: str
#   automount: str
#   deleteOnTermination: bool


class FilesystemsOptions(DiskOptions):
    pass


class BlockdevicemappingOptions(DiskOptions):
    pass


class HetznerCloudOptions(ResourceOptions):
    apiToken: str
    location: str
    serverName: str
    serverType: str
    labels: Mapping[str, str]
    # blockDeviceMapping: Mapping[str, BlockdevicemappingOptions]
    # serverNetworks: Sequence[NetworkOptions]
    # ipAddress: Optional[str]
    # fileSystemOptions: Optional[Mapping[str, FilesystemsOptions]]


class HetznerCloudMachineOptions(MachineOptions):
    hetznerCloud: HetznerCloudOptions
