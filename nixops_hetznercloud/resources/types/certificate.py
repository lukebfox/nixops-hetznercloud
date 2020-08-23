from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional


class HetznerCloudCertificateOptions(ResourceOptions):
    apiToken: str
    certificate: str
    privateKey: str
    labels: Mapping[str, str]
    certificateId: str
