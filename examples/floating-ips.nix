{ apiToken ? "changeme"
, location ? "nbg1" }:
{
  network.description = "Hetzner Cloud floating IP example deployment";

  machine1 =
    { resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
        ipAddresses = [
          # Assign a NixOps-managed floating IP resource.
          resources.hetznerCloudFloatingIPs.fip1
          # Or a pre-existing floating IP.
          "fip2"
        ];
      };
    };

  # Trivial floating IP resource.
  resources.hetznerCloudFloatingIPs.fip1 = { inherit apiToken location; };

  # Floating IPs can be created and not assigned to any server, useful if you
  # bring down your servers but still want to hang on to the address.
  resources.hetznerCloudFloatingIPs.fip3 = {
    inherit apiToken location;
    description = "Rainy day floating IP";
    ipType = "ipv4";
  };

}
