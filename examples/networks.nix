#{ apiToken ? "changeme" }:
let
  apiToken = "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx";
in
{
  network.description = "Hetzner Cloud network example deployment";

  resources.hetznerCloudNetworks.network1 = {
    inherit apiToken;
    ipRange = "10.1.0.0/16";
    subnets = ["10.1.0.0/24"];
  };

  resources.hetznerCloudNetworks.network2 = {
    inherit apiToken;
    ipRange = "10.2.0.0/16";
    subnets = [ "10.2.0.0/24" ];
  };

  machine0 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken;
        location = "nbg1";
        serverNetworks = [
          { network = resources.hetznerCloudNetworks.network1;
            privateIP = "10.1.0.2";
          }
          { network = resources.hetznerCloudNetworks.network2;
            privateIP = "10.2.0.2";
          }
        ];
      };
      programs.traceroute.enable = true;
    };

  machine1 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken;
        location = "fsn1";
        serverNetworks = [
          {  network = resources.hetznerCloudNetworks.network1;
             privateIP = "10.1.0.10";
          }
        ];
      };
      programs.traceroute.enable = true;
    };

  machine2 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken;
        location = "hel1";
        serverNetworks = [
          {  network = resources.hetznerCloudNetworks.network2;
             privateIP = "10.2.0.10";
          }
        ];
      };
      programs.traceroute.enable = true;
    };

}
