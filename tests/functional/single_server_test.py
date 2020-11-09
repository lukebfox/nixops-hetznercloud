from os import path

from nose import tools
from nose.plugins.attrib import attr

from tests.functional.generic_deployment_test import GenericDeploymentTest

parent_dir = path.dirname(__file__)

test_spec = "{0}/single_server_base.nix".format(parent_dir)


class SingleServerTest(GenericDeploymentTest):
    _multiprocess_can_split_ = True

    def setup(self):
        super(SingleServerTest, self).setup()
        self.depl.nix_exprs = [test_spec]

    def test_do_server(self):
        self.run_check()

    def check_command(self, command):
        self.depl.evaluate()
        machine = next(iter(self.depl.machines.values()))
        return machine.run_command(command)
