from nixops.resources import ResourceOptions
from typing import Mapping


class VolumeOptions(ResourceOptions):
    apiToken: str
    size: int
    format: str
    labels: Mapping[str, str]
    location: str
    volumeId: str
