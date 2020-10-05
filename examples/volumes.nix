{ apiToken ? "changeme"
, location ? "nbg1" }:
{
  network.description = "Hetzner Cloud volume example deployment";

  machine1 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
        # Here you can attach Volumes without mounting them.
#        volumes = [ resources.hetznerCloudVolumes.volume3; ];
      };

      # Mount a volume managed by NixOps.
      fileSystems."/data1".hetznerCloud.volume = resources.hetznerCloudVolumes.volume1;

      # Or a pre-existing volume. Note that fstype must now be given differently.
      fileSystems."/data2" = {
        fsType = "ext4";
        hetznerCloud.volume = "volume2";
      };

      fileSystems."/data3".hetznerCloud.volume = resources.hetznerCloudVolumes.volume3;

    };

  # Trivial volume resource.
  resources.hetznerCloudVolumes.volume1 = {
    inherit apiToken location;
    # default
    size = 21;
    # default  fsType = "ext4";
  };

  # Volumes can be created and not assigned to any server, useful if you
  # bring down your servers but still want to hang on to the volume.
  resources.hetznerCloudVolumes.volume3 = {
    inherit apiToken location;
    size = 17;
    fsType = "xfs";
  };

}
