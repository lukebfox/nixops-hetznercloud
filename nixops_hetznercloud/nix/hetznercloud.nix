# Configuration specific to the Hetzner Cloud backend.
{ config, lib, pkgs, name, uuid, resources, ... }:

with import ./lib.nix lib;
with lib;

let

  cfg = config.deployment.hetznerCloud;

  hetznercloud_dev_prefix = "/dev/disk/by-id/scsi-0HC_Volume_";

  commonHetznerCloudOptions =
    import ./common-hetznercloud-options.nix { inherit lib; };

  hetznerCloudServerNetworkOptions =
    { config, ... }:
    {
      options = {
        network = mkOption {
          example = literalExample "resources.hetznerCloudNetworks.privNet";
          type = resource "hetznercloud-network";
          apply = x: "nixops-${uuid}-${x._name}";
          description = ''
            A Network Resource which this Hetzner Cloud instance should become
            reachable on.
          '';
        };
        privateIP = mkOption {
          example = "10.1.0.2";
          type = types.str;
          description = ''
            The Hetzner Cloud instance's private IP address for this network.
          '';
        };
        aliasIPs = mkOption {
          default = [];
          example = [ "10.1.0.3" "10.1.0.4" "10.1.0.100" ];
          type = with types; listOf str;
          description = ''
            The Hetzner Cloud instance's alias IP addresses for this network.
          '';
        };
      };
    };

  hetznerCloudDiskOptions =
    { config, ... }:
    {

      imports = [ ./common-volume-options.nix ];
      
      options = {
        
        volume = mkOption {
          default = "";
          example = literalExample "resources.hetznerCloudVolumes.volume1";
          type = with types; either str (resource "hetznercloud-volume");
          apply = x: if builtins.isString x then x else "nixops-${uuid}-${x.name}";
          description = ''
            Hetzner Cloud identifier of the disk to be mounted. This can 
            be the name (e.g. ``volume1``) of a disk not managed by NixOps.
            It can also be a Volume resource (e.g. ``resources.hetznerCloudVolumes.db``).
          '';
        };

        mountPoint = mkOption {
          type = with types; str;
          description = "The mountpoint for this volume.";
        };

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
          ``deployment.hetznerCloud.volumes`` attribute entry.
        '';
      };
      config = mkAssert
        ( (config.hetznerCloud != null) || (config.device == null) )
        ''
        Configuring ``fileSystem.<name?>.device`` isn't supported for filesystems
        on mounted Hetzner Cloud Volumes. This option definition is calculated
        at runtime.
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
        Options are ``nbg1``, ``fsn1``, or ``hel1``.
      '';
    };

    deployment.hetznerCloud.serverName = mkOption {
      default = "nixops-${uuid}-${name}";
      example = "custom-server-name";
      type = types.str;
      description = ''
        The Hetzner Cloud Server Instance ``name``. This name
        must be unique within the scope of the Hetzner Cloud Project.
      '';
    };

    deployment.hetznerCloud.serverType = mkOption {
      default = "cx11";
      example = "cpx31";
      type = types.str;
      description = ''
        The Hetzner Cloud Server Instance type. A list of valid types can be
        found `here <https://www.hetzner.de/cloud#pricing>`_.
      '';
    };

    deployment.hetznerCloud.volumes = mkOption {
      default = [ ];
      example = [ { volume = "volume1"; } ];
      type = with types; listOf (submodule hetznerCloudDiskOptions);
      description = ''
        List of attached Volumes. ``fileSystems`` attributes which contain
        definitions for hetznerCloud options will get merged into this option
        definition during evaluation.
      '';
    };

    deployment.hetznerCloud.serverNetworks = mkOption {
      default = [];
      example = [];  # TODO
      type = with types; listOf (submodule hetznerCloudServerNetworkOptions);
    };

    deployment.hetznerCloud.ipAddresses = mkOption {
      default = [];
      example = "[resources.hetznerCloudFloatingIPs.fip1]";
      type = with types; listOf (either str (resource "hetznercloud-floating-ip"));
      apply = map (x: if builtins.isString x then x else "nixops-${uuid}-${x._name}");
      description = ''
        Hetzner Cloud Floating IP address resources to bind to.
      '';
    };
    
    deployment.hetznerCloud.labels = commonHetznerCloudOptions.labels;

    fileSystems = mkOption {
      type = with types; loaOf (submodule fileSystemsOptions);
    };

  };

  ##### implementation
  config = mkIf (config.deployment.targetEnv == "hetznercloud") {
    
    assertions = [
      { assertion = 3 >= length config.deployment.hetznerCloud.serverNetworks;
        message = "Hetzner Cloud Servers can only attach to up to three networks at once.";
      }
    ];
    
    nixpkgs.system = mkOverride 900 "x86_64-linux";
    services.openssh.enable = true;
    
    fileSystems = {};

    # note: this doesn't duplicate resource definition into the server definition eg size.
    deployment.hetznerCloud.volumes = mkFixStrictness
      (map
        (fs: {
          inherit (fs) mountPoint;
          inherit (fs.hetznerCloud) volume size;
          fsType = if fs.fsType != "auto" then fs.fsType else fs.hetznerCloud.fsType;
        })
        (filter (fs: fs.hetznerCloud != null) (attrValues config.fileSystems)));
  };

}
