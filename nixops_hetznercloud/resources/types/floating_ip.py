from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Union
from typing import Optional
from typing_extensions import Literal


class HetznerCloudFloatingIPOptions(ResourceOptions):
    apiToken: str
    name: str
    description: str
    protocol: Union[Literal["ipv4"], Literal["ipv6"]]
    location: Optional[Union[Literal["nbg1"], Literal["fsn1"], Literal["hel1"]]]
    labels: Optional[Mapping[str, str]]
