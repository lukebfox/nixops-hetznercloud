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
        # Here you can attach Volumes without mounting them.
        # These are not deleted automatically.
        # volumes = [ resources.hetznerCloudVolumes.volume1; ];
      };

      # Mount an volume managed by NixOps.
      fileSystems."/data1".hetznerCloud.volume = resources.hetznerCloudVolumes.volume1;

      # Or a pre-existing volume.
      fileSystems."/data2".hetznerCloud.volume = "volume2";
      
      # Leave volume undefined to automatically create it.
      # Can specify volume options or leave with defaults.
      # fileSystems."/data3" = {
      #   hetznerCloud.size = 20;
      #   hetznerCloud.deleteOnTermination = false;
      # };

    };

  resources.hetznerCloudVolumes.volume1 = {
    inherit apiToken location;
    size = 10;
    format = "ext4";
  };

}
