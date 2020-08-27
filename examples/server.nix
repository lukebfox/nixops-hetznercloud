{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx",
  location ? "nbg1"
}:
{
  network.description = "POC deployment";

  machine1 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
#        blockDeviceMapping = {
#          "/dev/sdb".volume = resources.hetznerCloudVolumes.volume1;
#        };
      };
    };

#  resources.hetznerCloudVolumes.volume1 = {
#    inherit apiToken location;
#    size = 10;
#    format = "ext4";
#  };

}
