# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Certificates.

from hcloud import APIException

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

    def show_type(self):
        return "{0}".format(self.get_type())


class CertificateState(HetznerCloudResourceState):
    """
    State of a Certificate.
    """

    _resource_type = "certificates"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + [
        "certificateId"
    ]

    @classmethod
    def get_type(cls):
        return "hetznercloud-certificate"

    def __init__(self, depl, name, id):
        HetznerCloudResourceState.__init__(self, depl, name, id)
        self.certificate_id = self.resource_id
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
        s = super(CertificateState, self).show_type()
        return "{0}".format(s)

    @property
    def resource_id(self):
        return self._state.get("certificateId", None)

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Certificate {0} [{1}]".format(self.resource_id, self.name)

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudCertificates"): attr}

    def get_physical_spec(self) -> Dict[str, Any]:
        return {"certificateId": self.resource_id}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudCertificates."

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self._state["certificateId"] = None
            self._state["certificate"] = None
            self._state["privateKey"] = None
            self._state["labels"] = None

    def _check(self) -> None:
        if self.resource_id is None:
            pass
        elif self.get_instance() is None:
            self.warn(" it needs to be recreated...")
            self.cleanup_state()
        elif self.state == self.STARTING:
            self.wait_for_resource_available(self.resource_id)

    def _destroy(self) -> None:
        instance = self.get_instance()
        if instance is not None:
            self.logger.log("destroying {0}...".format(self.full_name))
            instance.delete()
        self.cleanup_state()

    def realise_create_certificate(self, allow_recreate: bool) -> None:
        """
        Handle both create and recreate of the certificate resource.
        """
        config = self.get_defn()
        if self.state == self.UP:
            if not allow_recreate:
                raise Exception(
                    "{} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("certificate definition changed, recreating...")
            self._destroy()
            self._client = None

        name = self.get_default_name()
        self.logger.log("creating certificate '{}'...".format(name))
        try:
            bound_certificate = self.get_client().certificates.create(
                name=name,
                certificate=config.certificate,
                private_key=config.privateKey,
            )
            self.certificate_id = bound_certificate.id
        except APIException as e:
            if e.code == "invalid_input":
                raise Exception(
                    "couldn't create Certificate Resource due to {}".format(e.message)
                )
            else:
                raise e

        with self.depl._db:
            self.state = self.STARTING
            self._state["certificateId"] = self.certificate_id
            self._state["certificate"] = config.certificate
            self._state["privateKey"] = config.privateKey

        self.wait_for_resource_available(self.certificate_id)

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
