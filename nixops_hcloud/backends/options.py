from nixops.backends  import MachineOptions
from nixops.resources import ResourceOptions
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union
from typing_extensions import Literal


class HCloudOptions(ResourceOptions):
    name: str
    server_type: str
    volumes: Optional[Sequence[str]]
    networks: Optional[Sequence[str]]
    user_data: str
    labels: Optional[Mapping[str,str]]
    location: Union[Literal["Nuremberg"],Literal["Falkenstein"],Literal["Helsinki"]]
    

class HCloudMachineOptions(MachineOptions):
    hcloud: HCloudOptions
    
