from nixops.resources import ResourceOptions
from typing import Mapping


class SSHKeyOptions(ResourceOptions):
    apiToken: str
    publicKey: str
    labels: Mapping[str, str]
    sshKeyId: str
