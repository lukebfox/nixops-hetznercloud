# from socket import gethostname
# from getpass import getuser

import os

from hcloud import Client

# from nixops.util import attr_property
from nixops.deployment import Deployment
from nixops.state import StateDict

from typing import Optional


class HetznerCloudCommonState:
    depl: Deployment
    name: str
    _state: StateDict
    _client: Optional[Client]

    # Not always available
    api_token: Optional[str]

    COMMON_HCLOUD_RESERVED = ["apiToken"]

    #    def _retry(self, fun, **kwargs):
    #        return retry(fun, logger=self, **kwargs)

    #    labels = attr_property("hetznerCloud.labels", {},"json")

    #    def get_common_labels(self):
    #        labels = {
    #            "CharonNetworkUUID": self.depl.uuid,
    #            "CharonInstanceName": self.name,
    #            "CharonStateFile": "{0}@{1}:{2}".format(
    #                getuser(), gethostname(), self.depl._db.db_file
    #            ),
    #        }
    #        if self.depl.name:
    #            labels["CharonNetworkName"] = self.depl.name
    #        return labels

    #        def get_default_name_label(self):
    #        return "{0} [{1}]".format(self.depl.description, self.name)

    #    def update_labels_using(self, updater, user_labels={}, check=False):
    #        labels = {"Name": self.get_default_name_label()}
    #        labels.update(user_labels)
    #        labels.update(self.get_common_labels())

    #        if labels != self.labels or check:
    #            updater(labels)
    #            self.labels = labels

    #    def update_labels(self, id, user_labels={}, check=False):
    #        def updater(labels):
    #            # FIXME: handle removing tags.
    #            self._retry(lambda: self._conn.create_labels([id], labels))
    #
    #        self.update_labels_using(updater, user_labels=user_labels, check=check)

    def get_client(self):
        """
        Generic method to get a cached hcloud Hetzner Cloud client or create it.
        """
        new_api_token = (
            self.get_defn()["apiToken"] if self.depl.definitions else None  # type: ignore
        ) or os.environ.get("HCLOUD_API_TOKEN")
        if new_api_token is not None:
            self.api_token = new_api_token
        if self.api_token is None:
            raise Exception("please set ‘apiToken’ or $HCLOUD_API_TOKEN")
        if hasattr(self, "_client"):
            if self._client:
                return self._client
        self._client: Client = Client(token=self.api_token)
        # self._client: Client = connect(self.api_token)
        return self._client

    def reset_client(self):
        self._client = None
