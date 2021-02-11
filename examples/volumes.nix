{ apiToken ? "changeme"
, location ? "nbg1" }:
{
  network.description = "Hetzner Cloud volume example deployment";

  machine1 =
    { resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
        ## Defining a volume here instead of `fileSystems` lets you attach a volume unmounted.
        #volumes = [{ volume = resources.hetznerCloudVolumes.volume1; }];
      };

      # Mount a volume managed by NixOps.
      fileSystems."/data1".hetznerCloud.volume = resources.hetznerCloudVolumes.volume1;
      ## Or a pre-existing volume.
      #fileSystems."/data2" = {
      #  fsType = "ext4"; # must define fstype here for pre-existing volumes.
      #  hetznerCloud.volume = "volume2";
      #};

    };

  # Trivial volume resource.
  resources.hetznerCloudVolumes.volume1 = { inherit apiToken location; };

  # Volumes can be created and not assigned to any server, useful if you
  # bring down your servers but still want to hang on to the volume.
  resources.hetznerCloudVolumes.volume3 = {
    inherit apiToken location;
    size = 20;
    fsType = "xfs";
  };

}
