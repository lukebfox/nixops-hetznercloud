{
  description = "NixOps Hetzner Cloud Plugin: a plugin for NixOps deployments to the Hetzner Cloud provider";

  inputs.nixpkgs.url    = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.utils.url      = "github:numtide/flake-utils";
  inputs.flake-compat = {
    url = "github:edolstra/flake-compat";
    flake = false;
  };

  outputs = { self, nixpkgs, utils, ... }: utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs { inherit system; };

    pythonEnv = pkgs.poetry2nix.mkPoetryEnv {
      projectDir = ./.;
    };

  in rec {

    defaultPackage = packages.default;
    packages.default = pkgs.poetry2nix.mkPoetryApplication {
      projectDir = ./.;
      overrides = [
        pkgs.poetry2nix.defaultPoetryOverrides
        (import ./overrides.nix pkgs)
      ];
    };

    devShell = devShells.default;
    devShells.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.poetry
      ];
    };
  });

}
