import os.path
import nixops.plugins
from nixops.plugins import Plugin


class NixopsHetznerCloudPlugin(Plugin):
    @staticmethod
    def nixexprs():
        return [os.path.dirname(os.path.abspath(__file__)) + "/nix"]

    @staticmethod
    def load():
        return [
            "nixops_hetznercloud.resources",
            "nixops_hetznercloud.backends.hetznercloud",
        ]


@nixops.plugins.hookimpl
def plugin():
    return NixopsHetznerCloudPlugin()
