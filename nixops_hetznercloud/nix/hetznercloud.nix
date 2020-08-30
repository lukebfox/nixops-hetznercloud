# Configuration specific to the Hetzner Cloud backend.
{ config, lib, pkgs, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

let
    
  cfg = config.deployment.hetznerCloud;

  hetznercloud_dev_prefix = "/dev/disk/by-id/scsi-0HC_Volume_";

  commonHetznerCloudOptions = import ./common-hetznercloud-options.nix { inherit lib; };

  # hetznerCloudServerNetworkOptions =
  #   { config, ... }:
  #   {
  #     options = {
  #       subnetId = mkOption {
  #         example = "resources.hetznerCloudNetworkSubnets.subnet-1";
  #         type = resource "hetznercloud-network-subnet";
  #         description = ''
  #           The ID of a Subnet which contains this Hetzner Cloud instance.
  #         '';
  #       };
  #       privateIP = mkOption {
  #         example = "10.1.0.2";
  #         type = types.str;
  #         description = ''
  #           The Hetzner Cloud instance's private IP address on this Subnet.
  #         '';
  #       };
  #       aliasIPs = mkOption {
  #         default = [];
  #         example = [ "10.1.0.3" "10.1.0.4" "10.1.0.100"];
  #         type = with types; listOf str;
  #         description = ''
  #           The Hetzner Cloud instance's alias IP addresses on this Subnet.
  #         '';
  #       };
  #     };
  #     config = { };
  #   };

  hetznerCloudDiskOptions =
    { config, ... }:
    {
    
      imports = [ ./common-volume-options.nix ];
      
      options = {
        
        volume = mkOption {
          default = "";
          example = "volume1";
          type = with types; either str (resource "hetznercloud-volume");
          apply = x: if builtins.isString x then x else "nixops-" + uuid + "-" + x._name;
          description = ''
            Hetzner Cloud identifier of the disk to be mounted. This can 
            be the name (e.g. <literal>volume1</literal>) of a disk not 
            managed by NixOps. It can also be a Volume resource (e.g.
            <literal>resources.hetznerCloudVolumes.db</literal>).
            Leave empty to create a HetznerCloud volume automatically. 
          '';
        };

        mountPoint = mkOption {
          type = types.str;
          description = "The mountpoint for this volume.";
        };

        deleteOnTermination = mkOption {
          type = types.bool;
          description = ''
            For automatically created Hetzner Cloud volumes, determines whether the
            volume should be deleted on instance termination.
          '';
        };
      };
      
      config = {
        deleteOnTermination = mkDefault (config.volume == "");
      };
      
    };

  fileSystemsOptions =
    { config, ... }:
    {
      options.hetznerCloud = mkOption {
        default = null;
        type = with types; (nullOr (submodule hetznerCloudDiskOptions));
        description = ''
          Hetzner Cloud volume to be attached to this mount point. 
          This is shorthand for defining a separate
          <option>deployment.hetznerCloud.volumes</option> attribute
          entry.
        '';
      };
      config = mkAssert
        ( (config.hetznerCloud != null) || (config.device == null) )
        ''
        Configuring fileSystem.<name?>.device is not supported for filesystems
        on mounted Hetzner Cloud Volumes. This option definition is calculated runtime.
        ''
        {};
    };

in

{

  options = {

    deployment.hetznerCloud.apiToken = commonHetznerCloudOptions.apiToken;

    deployment.hetznerCloud.location = mkOption {
      default = null;
      example = "nbg1";
      type = with types; nullOr (enum ["nbg1" "fsn1" "hel1"]);
      description = ''
        The ID of the location to create the server in.
        Options are 'nbg1', 'fsn1', or 'hel1'.
      '';
    };

    deployment.hetznerCloud.serverName = mkOption {
      default = "nixops-${uuid}-${name}";
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
      type = types.str;
      description = ''
        The Hetzner Cloud Server Instance type. A list of valid types can be
        found at <link xlink:href='https://www.hetzner.de/cloud#pricing'/>
      '';
    };

    deployment.hetznerCloud.volumes = mkOption {
      default = [ ];
      example = [ { volume = "volume1"; } ];
      type = with types; listOf (submodule hetznerCloudDiskOptions);
      description = ''
        TODO
      '';
    };    

    # deployment.hetznerCloud.serverNetworks = mkOption {
    #   default = [];
    #   type = types.listOf (types.submodule hetznerCloudServerNetworkOptions);
    # };

    # deployment.hetznerCloud.ipAddress = mkOption {
    #   default = null;
    #   example = "resources.hetznerCloudFloatingIPs.exampleIP";
    #   type = types.nullOr (resource "hetznercloud-floating-ip");
    #   description = ''
    #     Hetzner Cloud Floating IP address resource to bind to.
    #   '';
    # };
    
    deployment.hetznerCloud.labels = commonHetznerCloudOptions.labels;

    fileSystems = mkOption {
      type = with types; loaOf (submodule fileSystemsOptions);
    };

  };

  ##### implementation
  config = mkIf (config.deployment.targetEnv == "hetznercloud") {
    nixpkgs.system = mkOverride 900 "x86_64-linux";
    services.openssh.enable = true;

    deployment.hetznerCloud.volumes = mkFixStrictness
      (map
        (fs: {
          inherit (fs) mountPoint;
          inherit (fs.hetznerCloud) volume size fsType deleteOnTermination;
        })
        (filter (fs: fs.hetznerCloud != null) (attrValues config.fileSystems)));
  };

}
