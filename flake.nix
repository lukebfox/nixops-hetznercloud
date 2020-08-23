{
  description = "nixops-hetznercloud: a [NixOps](https://nixos.org) plugin for deploying to [Hetzner Cloud](https://www.hetzner.com/cloud)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixops.url = "github:NixOS/nixops/master";
  inputs.utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs,
              nixops,
              utils }: utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;
#      overlays = [ (_:_: { nixops = nixops.defaultPackage.${system}; }) ];
    };
    
    overrides = pkgs.poetry2nix.overrides.withDefaults (_:_: {
      nixops = nixops.defaultPackage.${system};
    });
    
    # overrides = [pkgs.poetry2nix.defaultPoetryOverrides];

    # overrides = pkgs.poetry2nix.overrides.withDefaults (final: prev: {
    #   nixops = prev.nixops.overridePythonAttrs (
    #     { nativeBuildInputs ? [], ... }: {
    #       format = "pyproject";
    #       nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
    #     }
    #   );
    #   nixos-modules-contrib = prev.nixos-modules-contrib.overridePythonAttrs (
    #     { nativeBuildInputs ? [], ... }: {
    #       format = "pyproject";
    #       nativeBuildInputs = nativeBuildInputs ++ [ final.poetry ];
    #     }
    #   );
    # });


  in {
    devShell = pkgs.mkShell {
      buildInputs = [
        pkgs.poetry
        (pkgs.poetry2nix.mkPoetryEnv {
          inherit overrides;
          projectDir = toString ./.;
        })
      ];
    };
    
    defaultPackage = pkgs.poetry2nix.mkPoetryApplication {
      inherit overrides;
      projectDir = toString ./.;
      meta.description = "Nix package for ${system}";
    };

  });
}
