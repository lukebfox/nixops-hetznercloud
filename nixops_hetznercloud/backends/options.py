from nixops.backends import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional
from typing import Sequence


class HetznerCloudOptions(ResourceOptions):
    serverName: str
    serverType: str
    volumes: Optional[Sequence[str]]
    networks: Optional[Sequence[str]]
    user_data: str
    labels: Optional[Mapping[str, str]]
    location: Optional[str]
    datacenter: str


class HetznerCloudMachineOptions(MachineOptions):
    hetznerCloud: HetznerCloudOptions
