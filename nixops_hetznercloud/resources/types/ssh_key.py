from nixops.resources import ResourceOptions
from typing import Mapping


class HetznerCloudSSHKeyOptions(ResourceOptions):
    apiToken: str
    publicKey: str
    labels: Mapping[str, str]
    sshKeyId: str
