from nixops.resources import ResourceOptions
from typing import Mapping


class CertificateOptions(ResourceOptions):
    apiToken: str
    certificate: str
    privateKey: str
    labels: Mapping[str, str]
    certificateId: str
