[![CI](https://github.com/lukebfox/nixops-hetznercloud/workflows/CI/badge.svg)](https://github.com/lukebfox/nixops-hetznercloud/actions)
# NixOps Hetzner Cloud Plugin

[NixOps][1] is a tool for deploying [NixOS][2] machines to a local network or cloud provider. This repo contains a NixOps Plugin enabling [Hetzner Cloud][3] deployments.

## Disclaimer

This plugin is in alpha! That means it's a work in progress, and not meant for production. If like me, you're a nix-hobbyist and appreciate the affordable rates Hetzner provides but have been aching for a way to automate deployments then you're in luck! While you can already provision resources with the [Terraform provider][4], this will do nothing for automating your NixOS deployment. The alternative, NixOps, offers a more integrated solution which has just been waiting for someone to come and write a plugin. My goal is to automate the entire process of provisioning and deploying your NixOS box with one tool.

## Installing NixOps with plugins

There is no official method for this yet, however it is not difficult anymore. If you build your NixOS configurations with Flakes you can refer to [nixops-plugged][5] in your input to get access to a nixops with plugins. Here is a [solid example][6] from my own configs. If you don't use flakes, with the [original][7] is more appropriate.

## Usage

Before you can use NixOps to manage Hetzner Cloud Resources you must have a Hetzner Cloud account. You'll need to manually create any project which you want to be managed with NixOps, and generate a project-specific API token which NixOps will use for authentication (security>api tokens>generate api token).

Currently supported resources are as follows:

| Resource      | State |
|:--------------|:-----:|
| Server        | :heavy_check_mark: |
| Volume        | :heavy_check_mark: |
| Network       | :heavy_check_mark: |
| FloatingIP    | :heavy_check_mark: |
| Certificate   | :heavy_check_mark: |
| SSHKey        | :x: |
| LoadBalancer  | :x: |
| Firewall      | :x: |

All NixOps deployment options specific to Hetzner Cloud are declared in the nix files at `nixops_hetznercloud/nix`.

The example code introduces Hetzner Cloud resource management with NixOps.

## Developing

To start developing on the NixOps Hetzner Cloud plugin, you can run:

```bash
λ cd nixops-hetznercloud
λ nix develop # or `nix-shell`, if you have the old version of nix
λ poetry install
λ poetry shell
```

## Testing

From inside the development shell above, execute `pytest`. Remember to set the environmental variable `HCLOUD_API_TOKEN`.

## Updating Dependencies
There are times when you may want to update this project's dependencies.
- To get a more recent poetry/poetry2nix, you need to repin the nixpkgs flake input to the latest upstream commit by running `$ nix flake update --update-input nixpkgs`.
- To use your own local version of NixOps, or modify any python dependencies, edit `pyproject.toml` and run `poetry lock`.

---
Credit to the maintainers of the nixops-aws plugin which was a really useful model for nixops plugins and elitak for the original nixos-infect script.

[1]: https://github.com/NixOS/nixops
[2]: https://nixos.org/
[3]: https://www.hetzner.com/cloud
[4]: https://github.com/hetznercloud/terraform-provider-hcloud
[5]: http://github.com/lukebfox/nixops-plugged
[6]: https://github.com/lukebfox/the-nix-files/blob/master/flake.nix
[7]: https://github.com/typetetris/nixops-with-plugins
