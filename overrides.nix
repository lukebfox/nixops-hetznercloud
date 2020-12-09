pkgs:

self: super: {

  # https://github.com/nix-community/poetry2nix/issues/218
  packaging = super.packaging.overridePythonAttrs({buildInputs ? [], ...}: {
    format = "pyproject";
    buildInputs = buildInputs ++ [ self.flit-core ];
  });

  # https://github.com/nix-community/poetry2nix/issues/208
  typeguard = super.typeguard.overridePythonAttrs (old: {
    postPatch = ''
      substituteInPlace setup.py \
        --replace 'setup()' 'setup(version="${old.version}")'
    '';
  });

  nixops = super.nixops.overridePythonAttrs({ nativeBuildInputs ? [], ... }: {
    format = "pyproject";
    nativeBuildInputs = nativeBuildInputs ++ [ self.poetry ];
  });
}
