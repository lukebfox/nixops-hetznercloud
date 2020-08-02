{ config, lib, ... }:

with lib;

{
  options = {
    accessKeyId = mkOption {
      default = "";
      type = types.str;
      description = "The Hetzner Cloud API Token ID.";
    };
  };
}
