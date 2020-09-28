{
  description = "nixops-hetznercloud: a [NixOps](https://nixos.org) plugin for deploying to [Hetzner Cloud](https://www.hetzner.com/cloud)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixops.url = "github:NixOS/nixops/master";
  inputs.utils.url = "github:numtide/flake-utils";

  outputs = inputs: inputs.utils.lib.eachDefaultSystem (system: with inputs.nixpkgs.lib; let
    pkgs = import inputs.nixpkgs {
      inherit system;
    #  overlays = [(_:_:{ nixops = inputs.nixops.defaultPackage.${system}; })];
    };

   overrides = pkgs.poetry2nix.overrides.withDefaults (final: prev: {
    nixops = prev.nixops.overridePythonAttrs (
      { nativeBuildInputs ? [], ... }: {
        format = "pyproject";
        nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
      }
    );
   });
    
   #overrides = pkgs.poetry2nix.overrides.withDefaults (final: prev: {
   #  nixops = inputs.nixops.defaultPackage.${system};
   #});

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
