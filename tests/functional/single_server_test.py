from os.path import dirname
from tests.functional import GenericDeploymentTest


test_spec = f"{dirname(__file__)}/single_server_base.nix"


class SingleServerTest(GenericDeploymentTest):
    def setup(self) -> None:
        super(SingleServerTest, self).setup()
        self.depl.nix_exprs = [test_spec]

    def check_command(self, command) -> None:
        self.depl.evaluate()
        machine = next(iter(self.depl.machines.values()))
        return machine.run_command(command)

    def run_check(self) -> None:
        raise NotImplementedError

    def test_hetznercloud_server(self) -> None:
        self.run_check()
