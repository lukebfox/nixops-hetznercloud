# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Floating IPs.

import hcloud

# from nixops.diff import Handler
from nixops.resources import ResourceState, ResourceDefinition, DiffEngineResourceState
from nixops.util import attr_property

# import nixops_hetznercloud.resources
from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState

from .types.floating_ip import HetznerCloudFloatingIPOptions


class HetznerCloudFloatingIPDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud floating IP address.
    """

    config: HetznerCloudFloatingIPOptions

    @classmethod
    def get_type(cls):
        return "hetzner-cloud-floating-ip"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudFloatingIPs"

    def show_type(self):
        return "{0}".format(self.get_type())


class HetznerCloudFloatingIPState(DiffEngineResourceState, HetznerCloudCommonState):
    """
    State of a Hetzner Cloud Floating IP.
    """

    state = attr_property("state", ResourceState.MISSING, int)
    api_token = attr_property("apiToken", None)
    _reserved_keys = HetznerCloudCommonState.COMMON_HCLOUD_RESERVED + ["ipAddress"]

    @classmethod
    def get_type(cls):
        return "hetzner-cloud-floating-ip"

    def __init__(self, depl, name, id):
        ResourceState.__init__(self, depl, name, id)
        self._conn = None

    def show_type(self):
        s = super(HetznerCloudFloatingIPState, self).show_type()
        if self.state == self.UP:
            s = "{0} [{1}]".format(s, self.location)
        return s

    @property
    def resource_id(self):
        return self.addr_name

    @property
    def full_name(self):
        return "Hetzner Cloud floating IP address '{0}'".format(self.addr_name)

    def address(self):
        return self.connect().floating_ips.get_by_name(self.addr_name)

    def get_physical_spec(self):
        physical = {}
        if self.ip_address:
            physical["address"] = self.ip_address
        return physical

    def prefix_definition(self, attr):
        return {("resources", "hetznerCloudFloatingIPs"): attr}

    def create(self, defn, check, allow_reboot, allow_recreate):

        if self.state == self.UP and (self.location != defn.config["homeLocation"]):
            raise Exception("changing a floating IP's location isn't supported.")

        if self.state != self.UP:
            self.log(
                "creating {0} in {1}...".format(self.full_name, defn.config["location"])
            )

            response = self.get_client().floating_ips.create(
                type=defn.type,
                description=defn.description,
                labels=defn.labels,
                home_location=defn.location,
                name=defn.name,
            )

            try:
                response.action.wait_until_finished()

            except hcloud.ActionFailedException:
                raise Exception(
                    "Failed to create Floating IP resource with following error: {0}".format(
                        response.action.error
                    )
                )

            except hcloud.ActionTimeoutException:
                raise Exception(
                    "failed to create Hetzner Cloud floating IP;"
                    " timeout, maximium retries reached (100)"
                )

            self.state = self.UP
            self.location = defn.config["location"]
            self.ip_address = response.floating_ip.ip

        self.log("IP address is {0}".format(self.ip_address))

    def destroy(self, wipe=False):
        pass
