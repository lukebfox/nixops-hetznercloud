# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Certificates.

import hcloud
import time

from nixops.diff import Handler
from nixops.util import attr_property
from nixops.resources import ResourceDefinition, ResourceState, DiffEngineResourceState
from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState

from .types.certificate import HetznerCloudCertificateOptions


class HetznerCloudCertificateDefinition(ResourceDefinition):
    """
    Definition of a Certificate.
    """

    config: HetznerCloudCertificateOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-certificate"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudCertificates"

    def show_type(self):
        return "{0}".format(self.get_type())


class HetznerCloudCertificateState(DiffEngineResourceState, HetznerCloudCommonState):
    """
    State of a Certificate.
    """

    state = attr_property("state", ResourceState.MISSING, int)
    api_token = attr_property("apiToken", None)
    _reserved_keys = HetznerCloudCommonState.COMMON_HCLOUD_RESERVED + ["certificateId"]

    @classmethod
    def get_type(cls):
        return "hetznercloud-certificate"

    def __init__(self, depl, name, id):
        DiffEngineResourceState.__init__(self, depl, name, id)
        self.certificate_id = self._state.get("certificateId", None)
        self.handle_create = Handler(
            ["name", "certificate", "privateKey", "labels"],
            handle=self.realise_create_certificate,
        )

    def show_type(self):
        return super(HetznerCloudCertificateState, self).show_type()

    @property
    def resource_id(self):
        return self._state.get("certificateId", None)

    @property
    def full_name(self):
        return "Hetzner Cloud certificate {0} [{1}]".format(
            self._state["certificateId"], self._state["name"]
        )

    def prefix_definition(self, attr):
        return {("resources", "hetznerCloudCertificates"): attr}

    def get_physical_spec(self):
        return {"certificateId": self._state.get("certificateId", None)}

    def get_definition_prefix(self):
        return "resources.hetznerCloudCertificates."

    def _destroy(self):
        if self.state != self.UP:
            return
        self.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().certificates.get_by_id(
                self._state["certificateId"]
            ).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
            else:
                raise e

        self.cleanup_state()

    def cleanup_state(self):
        with self.depl._db:
            self.state = self.MISSING
            self._state["certificateId"] = None
            self._state["name"] = None
            self._state["certificate"] = None
            self._state["privateKey"] = None
            self._state["labels"] = None

    def _check(self):
        if self._state.get("certificateId", None) is None:
            return
        try:
            self.get_client().certificates.get_by_id(self._state["certificateId"])
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn(
                    "{0} was deleted from outside nixops,"
                    " it needs to be recreated...".format(self.full_name)
                )
                self.cleanup_state()
                return
        if self.state == self.STARTING:
            self.wait_for_certificate_available(self._state["certificateId"])

    def wait_for_certificate_available(self, certificate_id):
        while True:
            bound_certificate = self.get_client().certificates.get_by_id(
                certificate_id
            )
            if bound_certificate.created:
                break
            else:
                self.log_continue(".")
                time.sleep(1)
        self.log_end(" done")

        with self.depl._db:
            self.state = self.UP

    def realise_create_certificate(self, allow_recreate):
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

        self.log("creating certificate '{}'...".format(config["name"]))
        try:
            bound_certificate = self.get_client().certificates.create(
                name=config["name"],
                certificate=config["certificate"],
                private_key=config["privateKey"],
                labels=config["labels"],
            )
            self.certificate_id = bound_certificate.id
        except hcloud.APIException as e:
            if e.code == "invalid_input":
                raise Exception(
                    "couldn't create Certificate Resource due to {}".format(e.message)
                )
            else:
                raise e

        with self.depl._db:
            self.state = self.STARTING
            self._state["certificateId"] = self.certificate_id
            self._state["name"] = config["name"]
            self._state["certificate"] = config["certificate"]
            self._state["privateKey"] = config["privateKey"]
            self._state["labels"] = config["labels"]

        self.wait_for_certificate_available(self.certificate_id)

    def destroy(self, wipe=False):
        self._destroy()
        return True
