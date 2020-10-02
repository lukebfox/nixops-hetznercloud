import os.path
import nixops.plugins
from nixops.plugins import Plugin
from typing import List


class NixopsHetznerCloudPlugin(Plugin):
    @staticmethod
    def nixexprs() -> List[str]:
        return [os.path.dirname(os.path.abspath(__file__)) + "/nix"]

    @staticmethod
    def load() -> List[str]:
        return [
            "nixops_hetznercloud.resources",
            "nixops_hetznercloud.backends.hetznercloud",
        ]


@nixops.plugins.hookimpl
def plugin() -> Plugin:
    return NixopsHetznerCloudPlugin()
