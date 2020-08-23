from nixops.resources import ResourceOptions
from typing import Mapping


class HetznerCloudVolumeOptions(ResourceOptions):
    apiToken: str
    size: int
    format: str
    labels: Mapping[str, str]
    location: str
    volumeId: str
