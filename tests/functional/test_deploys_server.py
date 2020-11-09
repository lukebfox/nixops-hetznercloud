from nose import tools

from tests.functional.single_server_test import SingleServerTest


class TestDeploysNixos(SingleServerTest):
    def run_check(self):
        self.depl.deploy()
        self.check_command("test -f /etc/NIXOS")
