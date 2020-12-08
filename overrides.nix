pkgs:

self: super: {

  # https://github.com/nix-community/poetry2nix/issues/218
  packaging = super.packaging.overridePythonAttrs({buildInputs ? [], ...}: {
    format = "pyproject";
    buildInputs = buildInputs ++ [ self.flit-core ];
  });

  nixops = super.nixops.overridePythonAttrs({ nativeBuildInputs ? [], ... }: {
    format = "pyproject";
    nativeBuildInputs = nativeBuildInputs ++ [ self.poetry ];
  });
}
