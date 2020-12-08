{
  description = "NixOps Hetzner Cloud Plugin: a plugin for NixOps deployments to the Hetzner Cloud provider";

  inputs.nixpkgs.url    = "github:NixOS/nixpkgs/master";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";
  inputs.utils.url      = "github:numtide/flake-utils";

  inputs.flake-compat = {
    url = "github:edolstra/flake-compat";
    flake = false;
  };

  outputs = { self, nixpkgs, poetry2nix, utils, ...}: utils.lib.eachDefaultSystem (system: let

    pkgs = import nixpkgs {
      inherit system;
      # overlays = [ poetry2nix.overlay ];
    };

    overrides = pkgs.poetry2nix.overrides.withDefaults (import ./overrides.nix pkgs);

  in {

    defaultPackage = pkgs.poetry2nix.mkPoetryApplication {
      inherit overrides;
      projectDir = ./.;
    };

    devShell = pkgs.mkShell {
      buildInputs = [
        (pkgs.poetry2nix.mkPoetryEnv {
          inherit overrides;
          projectDir = ./.;
        })
        pkgs.poetry
      ];
    };
  });
}
