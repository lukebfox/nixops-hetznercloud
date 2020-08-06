# Configuration specific to the Hetzner Cloud backend.
{ config, lib, pkgs, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

let
    
  cfg = config.deployment.hetznerCloud;

#  hcloud_dev_prefix = "/dev/disk/by-id/scsi-0HC_Volume_";

  commonHetznerCloudOptions = import ./common-hetznercloud-options.nix { inherit lib; };

#  hetznerCloudServerNetworkOptions =
#    { config, ... }:
#    {
#      options = {
#        subnetId = mkOption {
#          example = "resources.hetznerCloudNetworkSubnets.subnet-1";
#          type = resource "hetzner-cloud-network-subnet";
#          description = ''
#            The ID of a Subnet which contains this Hetzner Cloud instance.
#          '';
#        };
#        privateIP = mkOption {
#          example = "10.1.0.2";
#          type = types.str;
#          description = ''
#            The Hetzner Cloud instance's private IP address on this Subnet.
#          '';
#        };
#        aliasIPs = mkOption {
#          default = [];
#          example = [ "10.1.0.3" "10.1.0.4" "10.1.0.100"];
#          type = with types; listOf str;
#          description = ''
#            The Hetzner Cloud instance's alias IP addresses on this Subnet.
#          '';
#        };
#      };
#      config = { };
#    };

#  fileSystemsOptions =
#    { config, ... }:
#    {
#      options = {
#        hcloud = mkOption {
#          default = null;
#          type = with types; (nullOr (submodule hcloudVolumeOptions));
#          description = ''
#            Hetzner Cloud Volume to be attached to this mount point. 
#            This is shorthand for defining a separate
#            <option>deployment.hetznerCloud.blockDeviceMapping</option>
#            attribute.
#          '';
#        };
#      };
#      config = mkIf (config.hetznerCloud != null) { };
#    };

in

{
  
  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {

    deployment.hetznerCloud.apiToken = mkOption {
      default = "";
      example = ''
        The Hetzner Cloud API Token which specifies the project to create this
        instance in. If left empty, it defaults to the contents of the
        environment variable <envar>HCLOUD_API_TOKEN</envar>.
      '';
    };

    deployment.hetznerCloud.location = commonHetznerCloudOptions.location;

    deployment.hetznerCloud.serverName = mkOption {
        default = "n-${shorten_uuid uuid}-${name}";
        example = "custom-server-name";
        type = types.str;
        description = ''
          The Hetzner Cloud Server Instance <literal>Name</literal>. This name
          must be unique within the scope of the Hetzner Cloud Project.
        '';
    };

    deployment.hetznerCloud.serverType = mkOption {
      default = "cx11";
      example = "cpx31";
      type = type.str;
      description = ''
        The Hetzner Cloud Server Instance type. A list of valid types can be
        found at <link xlink:href='https://www.hetzner.de/cloud#pricing'/>
      '';
    };

#    deployment.hetznerCloud.volumes = mkOption {
#      default = {};
#      example = { my-volume = "resources.hetznerCloudVolumes.my-volume" };
#      type = types.listOf (resource "hetzner-cloud-volume");
#    };

#    deployment.hetznerCloud.publicIp = mkOption {
#      default = null;
#      example = "resources.hetznerCloudFloatingIPs.exampleIP";
#      type = types.nullOr (resource "hetzner-cloud-floating-ip");
#      description = ''
#        Hetzner Cloud Floating IP address resource to bind to.
#      '';
#    };

#    deployment.hetznerCloud.serverNetworks = mkOption {
#      default = [];
#      type = types.listOf (submodule hetznerCloudServerNetworkOptions);
#    };
    
    deployment.hetznerCloud.labels = commonHetznerCloudOptions.labels;

#    fileSystems = mkOption {
#      type = with types; loaOf (submodule fileSystemOptions);
#    };

  };

  ##### implementation
  config = mkIf (config.deployment.targetEnv == "hetznerCloud") {
    nixpkgs.system = mkOverride 900 "x86_64-linux";
    services.openssh.enable = true;
  };

}
