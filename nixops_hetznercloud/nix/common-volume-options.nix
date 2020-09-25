# Options shared between the Volume resource type and the
# deployment.hetznercloud.volumes/fileSystems.*.hetznerCloud
# options in Hetzner Cloud instances.

{ config, lib, ... }:

with lib;

{

  options = {

    size = mkOption {
      default = 10;
      example = 50;
      type = with types; nullOr int;
      description = ''
        Size of the volume in GB. Standard limits are between 10GB and
        1024GB. It is possible to increase the upper limit to 10240GB
        on request.
      '';
    };
   
    fsType = mkOption {
      default = "ext4";
      example = "xfs";
      type = with types; nullOr (enum ["ext4" "xfs"]);
      description = ''
        The filesystem format for this volume.
        Choices are 'ext4' or 'xfs'.
      '';
    };

  };

}
