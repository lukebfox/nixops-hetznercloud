# Configuration specific to the Hetzner Cloud backend.
{ config, lib, pkgs, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

let
  
  cfg = config.deployment.hcloud;

  commonHCloudOptions = import ./common-hcloud-options.nix { inherit lib; };

  hcloudVolumeOptions =
    { config, ... }:
    {
      options = {
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
        
        filesystem = mkOption {
          default = "ext4";
          example = "xfs";
          type = types.enum ["ext4" "xfs"];
          description = ''
            The filesystem type for this volume.
            Choices are 'ext4' or 'xfs'.
          '';
        };
      };
      config = {};
    };
        

  hcloudServerNetworkOptions =
    { config, ... }:
    {
      options = {
        subnetId = mkOption {
          example = "resources.hcloudNetworkSubnets.subnet-1a";
          type = resource "hcloud-network-subnet";
          description = ''
            The ID of a Subnet which contains this Hetzner Cloud instance.
          '';
        };
        privateIP = mkOption {
          example = "10.1.0.2";
          type = types.str;
          description = ''
            The Hetzner Cloud instance's private IP address on this Subnet.
          '';
        };
        aliasIPs = mkOption {
          default = null;
          example = [];
          type = nullOr (resource "hcloud-floating-ip");
          description = ''
            The Hetzner Cloud instance's alias IP addresses on this Subnet.
          '';
        };
      };
      config = {};
    };


in

{
  
  imports = [ ./common-hcloud-auth-options.nix ];

  options = {

    deployment.hcloud.machineName = mkOption {
        default = "n-${shorten_uuid uuid}-${name}";
        example = "custom-machine-name";
        type = types.str;
        description = "The HCloud Instance <literal>Name</literal>.";
    };
    
    deployment.hcloud.location = commonHCloudOptions.location;
            
    deployment.hcloud.serverType = mkOption {
      default = "cx11";
      example = "cpx31";
      type = type.str;
      description = ''
        The Hetzner Cloud server type for this instance.
        List of valid server types can be found at TODO.
      '';
    };

    deployment.hcloud.volumes = mkOption {
      default = {};
      type = with types; attrsOf (submodule hcloudVolumeOptions);
    };
      
    deployment.hcloud.publicIp = mkOption {
      default = null;
      example = "resources.hcloudFloatingIPs.exampleIP";
      type = types.nullOr (resource "hcloud-floating-ip");
      description = ''
        Hetzner Cloud Floating IP address resource to bind to.
      '';
    };
    
    deployment.hcloud.serverNetworks = mkOption {
      default = {};
      type = with types; attrsOf (submodule hcloudServerNetworkOptions);
    };
    
    deployment.hcloud.labels = commonHCloudOptions.labels;
      
  };

  ##### implementation

  config = {};

}
