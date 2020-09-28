let
  apiToken = "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx";
  location = "nbg1";
in
{
  network.description = "Hetzner Cloud network example deployment";

  resources.hetznerCloudNetworks.network3 = {
    inherit apiToken;
    ipRange = "10.3.0.0/16";
    subnets = [ "10.3.0.0/24" ];
    routes = [
      { destination = "10.3.1.0/24";
        gateway = "10.3.0.2";
      }
    ];
  };

  resources.hetznerCloudFloatingIPs.fip1 = {
    inherit apiToken location;
    description = "static ip for example.com";
    type = "ipv4";
  };

}
