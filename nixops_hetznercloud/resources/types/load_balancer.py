from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Union
from typing import Optional
from typing_extensions import Literal


class LoadBalancerOptions(ResourceOptions):
    apiToken: str
    labels: Optional[Mapping[str, str]]
    location: Union[Literal["nbg1"], Literal["fsn1"], Literal["hel1"]]
