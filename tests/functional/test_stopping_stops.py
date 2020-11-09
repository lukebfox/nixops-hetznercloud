from nose import tools

from tests.functional.single_server_test import SingleServerTest


class TestStoppingStops(SingleServerTest):
    def run_check(self):
        self.depl.deploy()
        self.depl.stop_machines()
        m = list(self.depl.active.values())[0]
        tools.assert_equal(m.state, m.STOPPED)
