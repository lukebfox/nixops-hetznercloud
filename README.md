[![CI](https://github.com/lukebfox/nixops-hetznercloud/workflows/CI/badge.svg)](https://github.com/lukebfox/nixops-hetznercloud/actions)
# NixOps Hetzner Cloud Plugin

[NixOps][1] is a tool for deploying [NixOS][2] machines to a local network or cloud provider. 

This repo contains a NixOps Plugin enabling [Hetzner Cloud][3] deployments. While you can already provision resources with the [Terraform provider][4], this will do nothing for automating your NixOS deployment. The alternative, NixOps, offers a more integrated solution. The goal is to automate the entire process of provisioning and deploying your NixOS box with one tool. There is second Hetzner Cloud plugin at `nix-community/nixops_hcloud`, although it does not support as many features as this plugin, and requires bootstrapping.

## Installing NixOps with plugins

There is no official method for this yet, however it is not difficult anymore with [nixops-plugged][5]. Here is a [solid example][6] from my own configs.

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

The SSH key resource on Hetzner cloud exists purely to allow access to linux boxes when you first provision them. As this functionality is completely subsumed by Nix there's no point supporting this resource. The other resources could be supported although these are things which you can configure your NixOS boxes to handle using the array of packages/services in nixpkgs, so I'm open for contributions but I won't likely be writing these myself. 

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

From inside the development shell above, execute `pytest`. Remember to set the environmental variable `HCLOUD_API_TOKEN` to the token for the hetzner cloud project you're using asfor testing.

## Updating Dependencies
There are times when you may want to update this project's dependencies.
- To get a more recent poetry/poetry2nix, you need to repin the nixpkgs flake input to the latest upstream commit by running `nix flake update`.
- To use your own local version of NixOps or modify any python dependencies, edit `pyproject.toml` and run `poetry lock`.

---
Credit to the maintainers of the nixops-aws plugin which was a really useful model for nixops plugins and elitak for the original nixos-infect script.

[1]: https://github.com/nixos/nixops
[2]: https://nixos.org/
[3]: https://www.hetzner.com/cloud
[4]: https://github.com/hetznercloud/terraform-provider-hcloud
[5]: http://github.com/lukebfox/nixops-plugged
[6]: https://github.com/lukebfox/nix-configs/blob/master/flake.nix
[7]: https://github.com/typetetris/nixops-with-plugins
