# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Floating IPs.

import hcloud

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from .types.floating_ip import FloatingIPOptions


class FloatingIPDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud floating IP address.
    """

    config: FloatingIPOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-floating-ip"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudFloatingIPs"

    def show_type(self):
        return "{0}".format(self.get_type())


class FloatingIPState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Floating IP.
    """

    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + [
        "floatingIpId",
        "address",
    ]

    @classmethod
    def get_type(cls):
        return "hetznercloud-floating-ip"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.floating_ip_id = self.resource_id
        self.handle_create_floating_ip = Handler(
            ["location", "type"], handle=self.realise_create_floating_ip,
        )
        self.handle_modify_floating_ip_attrs = Handler(
            ["description", "labels"],
            after=[self.handle_create_floating_ip],
            handle=self.realise_modify_floating_ip_attrs,
        )

    def show_type(self):
        s = super(FloatingIPState, self).show_type()
        location = self._state.get("location", None)
        if self.state == self.UP:
            s = "{0} [{1}]".format(s, location)
        return s

    @property
    def resource_id(self):
        return self._state.get("floatingIpId", None)

    @property
    def full_name(self):
        return "Hetzner Cloud Floating IP {0} [{1}]".format(
            self.resource_id, self._state.get("address", None)
        )

    def prefix_definition(self, attr):
        return {("resources", "hetznerCloudFloatingIPs"): attr}

    def get_definition_prefix(self):
        return "resources.hetznerCloudFloatingIPs."

    def get_physical_spec(self):
        return {
            "floatingIpId": self.resource_id,
            "address": self._state.get("address", None),
        }

    def cleanup_state(self):
        with self.depl._db:
            self.state = self.MISSING
            self._state["floatingIpId"] = None
            self._state["address"] = None
            self._state["description"] = None
            self._state["labels"] = None
            self._state["location"] = None
            self._state["type"] = None

    def _check(self):
        if self.resource_id is None:
            return
        try:
            self.get_client().floating_ips.get_by_id(self.resource_id)
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn(
                    "{0} was deleted from outside nixops,"
                    " it needs to be recreated...".format(self.full_name)
                )
                self.cleanup_state()
                return
        if self.state == self.STARTING:
            self.wait_for_resource_available(
                self.get_client().floating_ips, self.resource_id
            )

    def _destroy(self):
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().floating_ips.get_by_id(self.resource_id).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
            else:
                raise e
        self.cleanup_state()

    def realise_create_floating_ip(self, allow_recreate):
        config = self.get_defn()

        if self.state == self.UP:
            if self._state["location"] != config.location:
                raise Exception("changing a floating IP's location isn't supported.")
            if not allow_recreate:
                raise Exception(
                    "{0} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("floating IP definition changed, recreating...")
            self._destroy()
            self._client = None

        location = self.get_client().locations.get_by_name(config.location)

        self.logger.log("creating floating IP at {0}...".format(location.description))
        try:
            response = self.get_client().floating_ips.create(
                name=self.get_default_name(), type=config.type, home_location=location,
            )
            if response.action:
                response.action.wait_until_finished()
            self.floating_ip_id = response.floating_ip.id
            self.address = response.floating_ip.ip
            self.logger.log("IP address is {0}".format(self.address))
        except hcloud.ActionFailedException:
            raise Exception(
                "Failed to create Hetzner Cloud floating IP resource "
                "with following error: {0}".format(response.action.error)
            )
        except hcloud.ActionTimeoutException:
            raise Exception(
                "failed to create Hetzner Cloud floating IP;"
                " timeout, maximium retries reached (100)"
            )

        with self.depl._db:
            self.state = self.STARTING
            self._state["floatingIpId"] = self.floating_ip_id
            self._state["location"] = config.location
            self._state["type"] = config.type
            self._state["address"] = self.address

        self.wait_for_resource_available(
            self.get_client().floating_ips, self.floating_ip_id
        )

    def realise_modify_floating_ip_attrs(self, allow_recreate):
        config = self.get_defn()

        self.logger.log("applying floating IP attribute changes")
        self.get_client().floating_ips.get_by_id(self.resource_id).update(
            description=config.description,
            labels={**self.get_common_labels(), **dict(config.labels)},
        )

        with self.depl._db:
            self._state["description"] = config.description
            self._state["labels"] = dict(config.labels)

    def destroy(self, wipe=False):
        self._destroy()
        return True
