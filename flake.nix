{
  description = "nixops-hetznercloud: a plugin for [NixOps](https://nixos.org) to deploy on [Hetzner Cloud](https://www.hetzner.com/cloud)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  inputs.utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs { inherit system; };
    
    overrides = pkgs.poetry2nix.overrides.withDefaults
      (final: prev: {
        nixops = prev.nixops.overridePythonAttrs (
          { nativeBuildInputs ? [], ... }: {
            format = "pyproject";
            nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
          }
        );
        nixos-modules-contrib = prev.nixos-modules-contrib.overridePythonAttrs (
          { nativeBuildInputs ? [], ... }: {
            format = "pyproject";
            nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
          }
        ); 
      });

  in {
    devShell = pkgs.mkShell {
      buildInputs = [
        pkgs.poetry
        (pkgs.poetry2nix.mkPoetryEnv {
          inherit overrides;
          projectDir = ./.;
        })
      ];
    };
    
    defaultPackage = pkgs.poetry2nix.mkPoetryApplication {
      inherit overrides;
      projectDir = ./.;
      meta.description = "Nix package for ${system}";
    };

  });
}
