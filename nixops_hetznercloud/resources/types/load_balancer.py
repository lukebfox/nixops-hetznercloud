from nixops.resources import ResourceOptions
from typing import Mapping, Optional, Sequence


class HealthCheckOptions(ResourceOptions):
    protocol: str
    port: int
    interval: int
    timeout: int
    retries: int
    http: Mapping[str, str]


class StickySessionOptions(ResourceOptions):
    cookieName: str
    cookieLifetime: int


class ServiceOptions(ResourceOptions):
    protocol: str
    listenPort: int
    destinationPort: int
    healthCheck: HealthCheckOptions
    proxyProtocol: bool
    stickySessions: StickySessionOptions
    certificates: str
    redirectHttp: bool


class TargetOptions(ResourceOptions):
    machine: str
    usePrivateIp: bool


class LoadBalancerOptions(ResourceOptions):
    apiToken: str
    algorithm: str
    enablePublicInterface: bool
    loadBalancerType: str
    network: Optional[str]
    services: Sequence[ServiceOptions]
    targets: Sequence[TargetOptions]
    location: str
    labels: Mapping[str, str]
