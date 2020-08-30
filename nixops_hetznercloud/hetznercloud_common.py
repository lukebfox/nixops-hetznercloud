# -*- coding: utf-8 -*-

import os
import re
import socket
import getpass
import time

from hcloud import Client, APIException
from hcloud.actions.client import BoundAction

from nixops.util import attr_property
from nixops.resources import ResourceState, DiffEngineResourceState

from typing import Dict


class HetznerCloudResourceState(DiffEngineResourceState):

    COMMON_HCLOUD_RESERVED = ["apiToken"]

    _resource_type: str

    state = attr_property("state", ResourceState.MISSING, int)
    api_token = attr_property("apiToken", None)

    def __init__(self, depl, name, id):
        DiffEngineResourceState.__init__(self, depl, name, id)
        self._client = None

    def get_common_labels(self) -> Dict[str, str]:
        labels = {
            "CharonNetworkUUID": self.depl.uuid,
            "CharonInstanceName": self.name,
            "CharonStateFileHost": socket.gethostname(),
            "CharonStateFileUser": getpass.getuser(),
        }
        pattern = "^$|(?i)((?=^[a-z0-9])[a-z0-9._-]{0,63}[a-z0-9]$)"
        file_name = os.path.basename(self.depl._db.db_file)
        if re.match(pattern, file_name):
            labels["CharonStateFileName"] = file_name
        if self.depl.name:
            labels["CharonNetworkName"] = self.depl.name
        return labels

    def get_default_name(self) -> str:
        return "nixops-{0}-{1}".format(self.depl.uuid, self.name)

    def get_default_name_label(self) -> str:
        return "{0} [{1}]".format(self.depl.description, self.name)

    def get_instance(self):
        try:
            subclient = getattr(self.get_client(), self._resource_type)
            return subclient.get_by_id(self.resource_id)
        except APIException as e:
            if e.code == "not_found":
                self.warn("{0} was deleted from outside nixops".format(self.full_name))
                return None
            else:
                raise

    def get_client(self) -> Client:
        """
        Generic method to get or create a Hetzner Cloud client.
        """
        new_api_token = (
            self.get_defn().apiToken if self.depl.definitions else None  # type: ignore
        ) or os.environ.get("HCLOUD_API_TOKEN")
        if new_api_token is not None:
            self.api_token = new_api_token
        if self.api_token is None:
            raise Exception("please set ‘apiToken’ or $HCLOUD_API_TOKEN")
        if hasattr(self, "_client"):
            if self._client:
                return self._client
        self._client = Client(token=self.api_token)
        return self._client

    def reset_client(self) -> None:
        self._client = None

    def wait_for_resource_available(self, resource_id: str, resource_type="") -> None:
        if resource_type == "":
            resource_type = self._resource_type
        while True:
            subclient = getattr(self.get_client(), resource_type)
            resource = subclient.get_by_id(resource_id)
            if resource.created is None:
                self.logger.log_continue(".")
                time.sleep(1)
            else:
                break
        self.logger.log_end(" done")

        with self.depl._db:
            self.state = self.UP

    def wait_with_progress(self, action: BoundAction, message: str) -> None:
        while action and action.progress < 100:
            self.logger.log_continue("{0}: {1}%\r".format(message, action.progress))
            time.sleep(1)
            action = self.get_client().actions.get_by_id(action.id)
