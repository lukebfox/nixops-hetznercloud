{ lib, ... }:

with lib;

{
  options = {
    apiToken = mkOption {
      default = "";
      type = types.str;
      description = "The Hetzner Cloud API Token ID.";
    };
  };
}
