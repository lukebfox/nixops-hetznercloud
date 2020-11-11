from tests.functional.single_server_test import SingleServerTest


class TestStopStops(SingleServerTest):
    def run_check(self):
        self.depl.deploy()
        self.depl.stop_machines()
        m = list(self.depl.active.values())[0]
        assert m.state == m.STOPPED
