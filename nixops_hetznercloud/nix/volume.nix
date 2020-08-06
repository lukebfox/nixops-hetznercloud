# Configuration specific to Hetzner Cloud Volume Resource.
{ config, lib, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-hetzner-cloud-auth-options.nix ];

  options = {
      
    name = mkOption {
      default = "nixops-${uuid}-${name}";
      example = "volume-1";
      type = types.str;
      description = ''
        The Hetzner Cloud Volume resource <literal>Name</literal>.;
      '';
    };

    size = mkOption {
      default = "10";
      example = "50";
      type = types.int;
      description = ''
        Size of the volume in GB. Standard limits are between 10GB and
        1024GB. It is possible to increase the upper limit to 10240GB
        on request. 
      '';
    };
   
    format = mkOption {
      default = "ext4";
      example = "xfs";
      type = types.enum ["ext4" "xfs"];
      description = ''
        The filesystem format for this volume.
        Choices are 'ext4' or 'xfs'.
      '';
    };
    
    location = mkOption {
      default = null;
      example = "nbg1";
      type = with types; nullOr (enum ["nbg1", "fsn1", "hel1" ]);
      description = ''
        The ID of the location to create the volume in.
        Ignored if serverId is set.  Options are 'nbg1', 'fsn1', or 'hel1'.
      '';
    };

    serverID = mkOption {
      default = null;
      example = "machines.webserver";
      type = types.nullOr machine
      description = ''
        The ID of the server to attach the volume to.
        Location of the server and the volume must be the same.
      '';
    };
    
    labels = (import ./common-hetznercloud-options.nix { inherit lib; }).labels;
    
  };

  config = {
  };
  
  config._type = "hetzner-cloud-volume"; 
  
}
