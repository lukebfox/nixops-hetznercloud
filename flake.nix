{
  description = "NixOps Hetzner Cloud Plugin: a plugin for NixOps deployments to the Hetzner Cloud provider";

  inputs.nixpkgs.url    = "github:NixOS/nixpkgs/master";
  inputs.utils.url      = "github:numtide/flake-utils";

  inputs.flake-compat = {
    url = "github:edolstra/flake-compat";
    flake = false;
  };

  outputs = { self, nixpkgs, utils, ...}: utils.lib.eachDefaultSystem (system: let

    pkgs = import nixpkgs { inherit system; };

    overrides = pkgs.poetry2nix.overrides.withDefaults (import ./overrides.nix pkgs);

  in {

    packages = rec {
      default = pkgs.poetry2nix.mkPoetryApplication {
        inherit overrides;
        projectDir = ./.;
      };
    };

    devShells = {
      default = pkgs.mkShell {
        buildInputs = [
          (pkgs.poetry2nix.mkPoetryEnv {
            inherit overrides;
            projectDir = ./.;
          })
          pkgs.python3Packages.poetry
        ];
      };
    };
  });
}
