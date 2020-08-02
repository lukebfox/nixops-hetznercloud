from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Sequence
from typing import Union
from typing import Optional


class HCloudServerOptions(ResourceOptions):
  name: str
  server_type: str
  volumes: Optional[Sequence[str]]
  networks: Optional[Sequence[str]]
  user_data: str
  labels: Optional[Mapping[str,str]]
  location: Optional[str]
  datacenter: str
