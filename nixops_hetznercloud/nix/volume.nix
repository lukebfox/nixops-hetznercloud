# Configuration specific to Hetzner Cloud Volume Resource.
{ config, lib, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-volume-options.nix ];

  options = {
    
    location = mkOption {
      default = null;
      example = "nbg1";
      type = with types; nullOr (enum ["nbg1" "fsn1" "hel1"]);
      description = ''
        The ID of the location to create the volume in.
        Ignored if serverId is set.  Options are 'nbg1', 'fsn1', or 'hel1'.
      '';
    };

    volumeId = mkOption {
      default = "";
      type = types.str;
      description = ''
        The Volume ID generated from Hetzner Cloud. This is set by NixOps
      '';
    };
    
  } // import ./common-hetznercloud-options.nix { inherit lib; };

  config._type = "hetznercloud-volume"; 
  
}
