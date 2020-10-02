[![CI](https://github.com/lukebfox/nixops-hetznercloud/workflows/CI/badge.svg)](https://github.com/lukebfox/nixops-hetznercloud/actions)
# NixOps Hetzner Cloud Plugin
  
[NixOps](https://github.com/NixOS/nixops) is a tool for deploying NixOS machines to a local network or cloud provider. 
This repo contains a NixOps Plugin enabling [Hetzner Cloud](https://www.hetzner.com/cloud) deployments.

## Disclaimer

This plugin is in alpha! That means it's a work in progress, and not meant for production. If like me, you're a nix-hobbyist and appreciate the affordable rates Hetzner provides but have been aching for a way to automate deployments then you're in luck! While you can already provision resources with the [Terraform provider](https://github.com/hetznercloud/terraform-provider-hcloud), this will do nothing for automating your NixOS deployment. The alternative, NixOps, offers a more integrated solution which has just been waiting for someone to come and write a plugin. My goal is to automate the entire process of provisioning and deploying your NixOS box with one tool. At the moment I'm working on the remaining resource types with an intent to support all of them.

## Installing NixOps with plugins

There is no official method for this yet, however it is not difficult anymore. If you build your NixOS configurations with Flakes you can refer to [lukebfox/nixops-with-plugins](http://github.com/lukebfox/nixops-with-plugins) which comes with the [AWS](http://github.com/NixOS/nixops-aws), [GCE](http://github.com/nix-community/nixops-gce), Hetzner Cloud and [VBox](http://github.com/nix-community/nixops-vbox) plugins installed. Here is a [solid example](https://github.com/lukebfox/nix-infrastructure/) of this from my own configs. If you don't use flakes, with a little love the [original](https://github.com/typetetris/nixops-with-plugins) will have you covered.

## Usage

Before you can use NixOps to manage Hetzner Cloud Resources you must have a Hetzner Cloud account. You'll need to manually create any project which you want to be managed with NixOps, and generate a project-specific API token which NixOps will use for authentication (security>api tokens>generate api token). The example code introduces Hetzner Cloud resource management with NixOps.

| Resources    | Status |
|--------------|--------|
| Server       | DONE   |
| Volume       | DONE   |
| Network      | DONE   |
| FloatingIP   | DONE   |
| Certificate  | DONE   |
| LoadBalancer | TODO   |
| SSHKey       | TODO   |

The NixOps deployment options specific to Hetzner Cloud are declared in the nix files.

## Developing

To start developing on the NixOps Hetzner Cloud plugin, you can run:

```bash
  $ nix develop
  $ poetry install
  $ poetry shell
```

## Testing

Aside from the testing during development, There isn't much in the way of testing at the moment. I think this is key to have as soon as the core functionality is built, and will have my eye on this soon.

---
Credit to the maintainers of the nixops-aws plugin which was a really useful model for nixops plugins and elitak for the original nixos-infect script.
