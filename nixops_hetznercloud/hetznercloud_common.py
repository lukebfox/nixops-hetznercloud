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

from typing import Dict, Any, Optional, Type, TypeVar


TypedResource = TypeVar("TypedResource")


class HetznerCloudResourceState(DiffEngineResourceState):

    COMMON_HCLOUD_RESERVED = ["resourceId", "apiToken"]

    _resource_type: str
    _client: Optional[Client]

    state = attr_property("state", ResourceState.MISSING, int)
    resource_id = attr_property("resourceId", None)
    api_token = attr_property("apiToken", None)

    def __init__(self, depl, name, id):
        DiffEngineResourceState.__init__(self, depl, name, id)
        self.resource_id = None
        self._client = None

    def get_physical_spec(self) -> Dict[str, Any]:
        return {"resourceId": self.resource_id}

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
        return f"nixops-{self.depl.uuid}-{self.name}"

    def get_default_name_label(self) -> str:
        return f"{self.depl.description} [{self.name}]"

    @property
    def full_name(self) -> str:
        raise NotImplementedError

    def get_hetznercloud_resource(
        self, name: str, type_name: str, type: Type[TypedResource]
    ) -> TypedResource:
        if name.startswith("nixops-" + self.depl.uuid):
            name = name.split("-")[6]
        return self.depl.get_typed_resource(name, type_name, type)

    def get_instance(self) -> Any:
        try:
            subclient = getattr(self.get_client(), self._resource_type)
            return subclient.get_by_id(self.resource_id)
        except APIException as e:
            if e.code == "not_found":
                return None
            else:
                raise

    def get_client(self) -> Client:
        """
        Generic method to get or create a Hetzner Cloud client.
        """

        if hasattr(self, "_client"):
            if self._client:
                return self._client

        new_api_token = (
            self.get_defn().config.apiToken
            if self.name in (self.depl.definitions or [])
            else None  # type: ignore
        ) or os.environ.get("HCLOUD_API_TOKEN")

        if new_api_token is not None:
            self.api_token = new_api_token

        if self.api_token is None:
            raise Exception("please set ‘apiToken’ or $HCLOUD_API_TOKEN")

        self._client = Client(token=self.api_token)
        return self._client

    def realise_modify_labels(self, allow_recreate: bool) -> None:
        defn = self.get_defn().config

        self.logger.log(f"updating labels for {self.full_name}")
        self.get_instance().update(
            labels={**self.get_common_labels(), **dict(defn.labels)}
        )

        with self.depl._db:
            self._state["labels"] = dict(defn.labels)

    def wait_for_resource_available(
        self, resource_id: str, resource_type: str = ""
    ) -> None:
        if resource_type == "":
            resource_type = self._resource_type
        while True:
            res = getattr(self.get_client(), resource_type).get_by_id(resource_id)
            if res.created is None:
                self.logger.log_continue(".")
                time.sleep(1)
            else:
                break
        self.logger.log_end(" done")

        with self.depl._db:
            self.state = self.UP

    def wait_on_action(self, action: BoundAction) -> None:
        while action.status == "running":
            self.logger.log_continue(".")
            time.sleep(1)
            action = self.get_client().actions.get_by_id(action.id)
        self.logger.log_end("")
        if action.status != "success":
            raise Exception(f"unexpected status: {action.status}")

    def cleanup_state(self) -> None:
        """Discard all state pertaining to an instance"""
        raise NotImplementedError

    def _check(self) -> None:
        if self.resource_id is None:
            return
        instance = self.get_instance()
        if instance is None:
            self.warn(
                f"{self.full_name} was deleted from outside nixops;"
                "it needs to be recreated..."
            )
            self.cleanup_state()
        elif self.state == self.STARTING:
            self.wait_for_resource_available(self.resource_id)

    def _destroy(self) -> None:
        instance = self.get_instance()
        if instance is not None:
            self.logger.log(f"destroying {self.full_name}...")
            instance.delete()
        self.cleanup_state()

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
