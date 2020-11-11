from os.path import dirname, abspath
from nixops.plugins import Plugin, hookimpl
from typing import List


class NixopsHetznerCloudPlugin(Plugin):
    @staticmethod
    def nixexprs() -> List[str]:
        return [dirname(abspath(__file__)) + "/nix"]

    @staticmethod
    def load() -> List[str]:
        return [
            "nixops_hetznercloud.resources",
            "nixops_hetznercloud.backends.hetznercloud",
        ]


@hookimpl
def plugin() -> Plugin:
    return NixopsHetznerCloudPlugin()
