from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional


class HetznerCloudCertificateOptions(ResourceOptions):
    apiToken: str
    name: str
    certificate: str
    privateKey: str
    labels: Optional[Mapping[str, str]]
    certificateId: str
