{
  description = "nixops-hetznercloud: a [NixOps](https://nixos.org) plugin for deploying to [Hetzner Cloud](https://www.hetzner.com/cloud)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/master";
  inputs.utils.url = "github:numtide/flake-utils";

  outputs = inputs: inputs.utils.lib.eachDefaultSystem (system: let

    pkgs = import inputs.nixpkgs { inherit system; };

    overrides = pkgs.poetry2nix.overrides.withDefaults (final: prev: {
      nixops = prev.nixops.overridePythonAttrs (
        { nativeBuildInputs ? [], ... }: {
          format = "pyproject";
          nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
        }
      );
    });

  in {
    
    defaultPackage = pkgs.poetry2nix.mkPoetryApplication {
      inherit overrides;
      projectDir = ./.;
      meta.description = "Nix package for ${system}";
    };

    devShell = pkgs.mkShell {
      buildInputs = [
        pkgs.poetry
        (pkgs.poetry2nix.mkPoetryEnv {
          inherit overrides;
          projectDir = ./.;
        })
      ];
    };


  });

}
