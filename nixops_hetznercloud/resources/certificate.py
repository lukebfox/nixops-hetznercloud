# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Certificates.

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence

from .types.certificate import CertificateOptions


class CertificateDefinition(ResourceDefinition):
    """
    Definition of a Certificate.
    """

    config: CertificateOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-certificate"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudCertificates"


class CertificateState(HetznerCloudResourceState):
    """
    State of a Certificate.
    """

    definition_type = CertificateDefinition

    _resource_type = "certificates"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED

    @classmethod
    def get_type(cls):
        return "hetznercloud-certificate"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.handle_create_certificate = Handler(
            ["certificate", "privateKey"],
            handle=self.realise_create_certificate,
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            after=[self.handle_create_certificate],
            handle=super().realise_modify_labels,
        )

    def show_type(self):
        return f"{super(CertificateState, self).show_type()}"

    @property
    def full_name(self) -> str:
        return f"Hetzner Cloud Certificate {self.resource_id}"

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudCertificates"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudCertificates."

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self._state["certificate"] = None
            self._state["privateKey"] = None
            self._state["labels"] = None

    def realise_create_certificate(self, allow_recreate: bool) -> None:
        """
        Handle both create and recreate of the certificate resource.
        """
        defn: CertificateOptions = self.get_defn().config

        if self.state == self.UP:
            if not allow_recreate:
                raise Exception(
                    f"{self.full_name} definition changed and it needs to be"
                    "recreated use --allow-recreate if you want to create a new one"
                )
            self.warn("certificate definition changed, recreating...")
            self._destroy()
            self._client = None

        name = self.get_default_name()
        self.logger.log(f"creating certificate '{name}'...")
        self.resource_id = (
            self.get_client()
            .certificates.create(
                name=name,
                certificate=defn.certificate,
                private_key=defn.privateKey,
            )
            .id
        )

        with self.depl._db:
            self.state = self.STARTING
            self._state["certificate"] = defn.certificate
            self._state["privateKey"] = defn.privateKey

        self.wait_for_resource_available(self.resource_id)
