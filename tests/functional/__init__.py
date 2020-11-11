from nixops.statefile import StateFile
from nixops.deployment import Deployment

from tests import db_file


class DatabaseUsingTest(object):
    def setup(self) -> None:
        self.sf = StateFile(db_file)

    def teardown(self) -> None:
        self.sf.close()


class GenericDeploymentTest(DatabaseUsingTest):
    def setup(self) -> None:
        super(GenericDeploymentTest, self).setup()
        self.depl: Deployment = self.sf.create_deployment()
        self.depl.logger.set_autoresponse("y")
