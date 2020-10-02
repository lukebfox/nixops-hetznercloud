let
  apiToken = "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx";
  location = "nbg1";
  

in
{
  network.description = "Hetzner Cloud test deployment";

   machine2 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken;# location;
        location = "fsn1";
        serverType = "cx11";
      };
    };

  # resources.hetznerCloudVolumes.volume1 = {
  #   inherit apiToken location;
  #   size = 10;
  #   fsType = "ext4";
  # };

  # resources.hetznerCloudNetworks.network1 = {
  #   inherit apiToken;
  #   ipRange = "10.3.0.0/16";
  #   subnets = [ "10.3.0.0/24" ];
  #   routes = [
  #     { destination = "10.3.1.0/24";
  #       gateway = "10.3.0.2";
  #     }
  #   ];
  # };

  # resources.hetznerCloudFloatingIPs.fip1 = {
  #   inherit apiToken location;
  #   description = "static ip for example.com";
  #   type = "ipv4";
  # };

#   resources.hetznerCloudCertificates.cert2 = {
#     inherit apiToken location;
#     certificate = ''
# -----BEGIN CERTIFICATE-----
# MIIC1TCCAb2gAwIBAgIJAJ2MDJy9Bw+tMA0GCSqGSIb3DQEBBQUAMBoxGDAWBgNV
# BAMTD3d3dy5leGFtcGxlLmNvbTAeFw0yMDA4MDUxNTM0NTdaFw0zMDA4MDMxNTM0
# NTdaMBoxGDAWBgNVBAMTD3d3dy5leGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEB
# BQADggEPADCCAQoCggEBAK8xiGziGDozvOFtlHLpZWMIDAy5dCqrVsaD2cPRWkjO
# OlQKwid1pq86sse7N7TOI/12zNWTnxUFZUKpqGcqxv9P/iuBgvfSC+b0ONndLBBJ
# W67O82pA48HEF/xdKwLnTG3toBYrhMqWm7x1vywlM/Otiaj/Rd5wYXduWZ5mkymu
# TeXF0Yx2cm9Pz5NgvgoD8CF6mIqnYuvSDefNGjC0RlUVxAp/tQn3m6gLD3nhzefs
# hpksBMOp9ct8TYK9+gNVcI1mEj6McYKSYLrF9Oko5SJwbJdrJHt9tr+CIz8q8hax
# jpfrri2kCl6+CyIP69MeWH5IetwUaZ9/Kh01Ljfw4qkCAwEAAaMeMBwwGgYDVR0R
# BBMwEYIPd3d3LmV4YW1wbGUuY29tMA0GCSqGSIb3DQEBBQUAA4IBAQBAr/bJDUcK
# VHuM0S9AUJZHGnZWdsXEdCScgmvaRfSwBV/O2cFerIZt7dirEW/x57rKsR2z5UHa
# SigSUrAVUaDurIGsKCjbX9xfVKpHuZ2AciWCt8gC/vLqUonaDQ6+7orlIROHhow0
# JfaFTapZ6DyY/m4wLCKHaLXNdRZ0cuuW+bYvlnwqDDZTJhpuWIfybHECUY8DbAlc
# TbVvQkuphAR3BSPZKncVV5viRCnugCBU3/yquSxzUY2XvbBam9f0yYUzW2dhKOKO
# teZ5g0+6T8ZdvsIO6dPxiVk7bxLCYA7S7NeawhIKuu/2uxSe8gJJOUDFcorj7Mxp
# DebQbjU9qNHd
# -----END CERTIFICATE-----
#     '';
#     privateKey = ''
# -----BEGIN RSA PRIVATE KEY-----
# MIIEpAIBAAKCAQEArzGIbOIYOjO84W2UcullYwgMDLl0KqtWxoPZw9FaSM46VArC
# J3Wmrzqyx7s3tM4j/XbM1ZOfFQVlQqmoZyrG/0/+K4GC99IL5vQ42d0sEElbrs7z
# akDjwcQX/F0rAudMbe2gFiuEypabvHW/LCUz862JqP9F3nBhd25ZnmaTKa5N5cXR
# jHZyb0/Pk2C+CgPwIXqYiqdi69IN580aMLRGVRXECn+1CfebqAsPeeHN5+yGmSwE
# w6n1y3xNgr36A1VwjWYSPoxxgpJgusX06SjlInBsl2ske322v4IjPyryFrGOl+uu
# LaQKXr4LIg/r0x5Yfkh63BRpn38qHTUuN/DiqQIDAQABAoIBAEUE86VJ0ZekaGY7
# QH+g+aNxOSYOLfjddZtRuIoPwUzrikkvz9ux2xAvxN0xIbomeEFT+1CtDsA+Vu1T
# X5f9X1aYUh8br9goNS4wyvDx1Hk6HVeaCoWyuMfOlFCE9/v12cN5GVeCn5ccjJBL
# pxwiL/xxQsmEgCcpCQz/OWlRKesCLKUsAqqMFZV9gqO2wnKyZqjnufY1jxv2zfNs
# AfOXMp5EbmfkSqOEgXYiufuS3eMypSVPTEbbWgYFR6EcLfuw01Tf5rIcOA+bYTEs
# Ewxkzkf+4eedYcDUHhUO1mcCOaroML13lP/QQl1ULdS/PSywTq+tZoJg94+uoO5c
# g4KiH20CgYEA1yMuxKo1JIu6FBWRB1kNhXVfiR91hShaDtS9F88mEGX3ve72/CIm
# k/E3VY5Aow+Tshxq2w8/m4pGHKwrcVhetUeb84t7Ka0v6usG39Yosm1zdCiRSph/
# JiJmzoWd08ZUTJcwB2CVepaN6YP8c9P0NqAaNE7xVMp+hHETThd+amsCgYEA0Hge
# 3DHbS6wWtS7ke/0m/NQy6FVvi6GFH/sO7MKS9T4pHL2e2QNFLT8mI9npogFNIvnw
# bsMuzZ04tnOFi0bcryOwXVLZ+NdNxOtT6rjLPow0le5CGH0yUCdEAiSPPlQnPlFc
# LHau5fLv1veCoOraf/F5j0gGBUTIzH2L4UP6FDsCgYA4974IobGUzdMmQle3BGPK
# NTxpCQWLjxXZ24d+6IGB0h56Eu8f8MMaZcNrSlHfW96WSWQaQb1sKH9MVGLkjqv1
# gNLQ+NxSOuP3ZujZGNKJ/OWXmq5ufFce9/kVMtiKHXhxF4/GRFMQtRE7BpIw8a03
# UcnelBDfjQdXdsHP6fS1pQKBgQCzTz6sAy4urnxxpz3b7+kC+ro24JWrMmjBEz7J
# IqsoyiiukeL5ojh0LKbvm1W7hQcGGJlXjAbL0HmhZUfufir/ceEWxFa8FOTNheSO
# NhiLWik49NBhI/6MttlmRm/3GocOsQhpLkRNgWIOMqJnKtp5xgfa2AZlrb5RNYOF
# ZOTLVQKBgQCMEvGeBDZv0o57Tp0Tte2Tsg6zYdgGtl0PCERWYvREs0UEBNHBVNw4
# 7N+XTx19158d1T6MVk+vEb2+eR+q/TKX6IA2FaAWKPsa1rzi3yvVrhjOUfEiOAuN
# JzjAuZDiBsopM6mCdvw2IjUL3sSQt/bzsEsFyHuXvAqUe7IL6frY/w==
# -----END RSA PRIVATE KEY-----
#     '';
#   };

#   resources.hetznerCloudCertificates.cert2 = {
#     inherit apiToken location;
#     certificate = ''
# -----BEGIN CERTIFICATE-----
# MIICwzCCAaugAwIBAgIJAJUFoYj4Q1sMMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNV
# BAMTCWRpdHRvLmNvbTAeFw0yMDEwMDIwMzMyMDBaFw0zMDA5MzAwMzMyMDBaMBQx
# EjAQBgNVBAMTCWRpdHRvLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
# ggEBAMhz3Zq3iqGJ756x0hXY4I98NPW8nWZZb6gvnTzEihKGdasvMtMSpsd+K+sT
# 4JxBOSxamULHiJfdND9BkVwfniSnAdkGtiV1kHBVx62iD/g+quc3yxYQKc6ROv4q
# N8j0tQrJEtnkEKZwunt8It/jfkLc3S/ctpBfwQHQqcatnTCR8WqZzPyaENYtR3Fk
# zJjFkHVWOBPvzQ5heWUatCotgakQ0T7doFucafhShCdiQ4p6d4z31Q8x4QnZr57M
# Ga5oWEoV1mhAiFLWiz/Jwe1OotZ5+3EM0KfyVLEURK69XD2M/G7zK40Eypqpiyp0
# YAxLbRiR3z0kjpfuyz7Jmuw2S+0CAwEAAaMYMBYwFAYDVR0RBA0wC4IJZGl0dG8u
# Y29tMA0GCSqGSIb3DQEBBQUAA4IBAQBpEZb6JavQOGRi6mDU98knYaZeXcGAaRr5
# 0lAVsbTjFJrb0uIHmzgiB1F3GLI+JfnLKkNy9qPRd2hU3H3GknozEi1lq3sN0YBo
# N6anlpCGCJ/b1FqvOvjsVgwMdqUnxItPxPp1umWdSzgwDXlNR/sgmV9t+AMZNDSj
# //DV1NP12dV81D3jzL44a/MQpSiD6jOoaaJXsCMiPNPZd5FAgu2zVVcXnOAILySR
# Ljw6ln+4ujZfReNMchjP4zB1nE7I7plGhy6kxg6wtmhjseHOhPA1j2IZhpaoTofE
# BCIbwtJ+lRDkzd8n0Yh9Vh+AsnuyhEsw0qH4EaH5ud815ZB/j9Dx
# -----END CERTIFICATE-----
#     '';
#     privateKey = ''
# -----BEGIN RSA PRIVATE KEY-----
# MIIEpAIBAAKCAQEAyHPdmreKoYnvnrHSFdjgj3w09bydZllvqC+dPMSKEoZ1qy8y
# 0xKmx34r6xPgnEE5LFqZQseIl900P0GRXB+eJKcB2Qa2JXWQcFXHraIP+D6q5zfL
# FhApzpE6/io3yPS1CskS2eQQpnC6e3wi3+N+QtzdL9y2kF/BAdCpxq2dMJHxapnM
# /JoQ1i1HcWTMmMWQdVY4E+/NDmF5ZRq0Ki2BqRDRPt2gW5xp+FKEJ2JDinp3jPfV
# DzHhCdmvnswZrmhYShXWaECIUtaLP8nB7U6i1nn7cQzQp/JUsRRErr1cPYz8bvMr
# jQTKmqmLKnRgDEttGJHfPSSOl+7LPsma7DZL7QIDAQABAoIBAHTeqPuFu3wHcf+y
# aWx3cCX4IuCLQbHkvybt69z8Mgwu/Pf7osRRgY+aTnzWsAQqOu1TPTwkHc19GPMw
# hVGS1Z9FB9zC/vvEGZyFRtBDRtBTqUz5yJxqfBWFs0Fw1+mAUvWg2i7Tu6lu3CsW
# 6zZh6sGNCCDZrE9spJksUXAW1Sj1RUH5KxRxxM8jKYjDgKKwdOKn3aW68BbRAF8f
# ug2SAgUmcvHqzbA0Zb5RCEuK1xHO2SbxvlEhDOtW0BipIVsTaATi9oSdT4MKItHk
# G7vHgP4nrA2BYAS2y/OI5p44CR4mWhBSwU8h2gi4uvr2v6Qb7KoOjKTjeQNfOB8P
# oPWTeXkCgYEA9IHT74sbytNUiSpuKZb7gdw19z4fXYUCh894eI9AGk//wD0wG/XO
# Jl1u97+MAvE3GPjL/cuIYUwWdsdXPLN3XpsmaV/n5kI1X04i16SIzdP3Rl5ddIja
# jgpLw0qlkdTLCzfb8nkPiztETc5LEXT4w3er4z6HI4TZoLWJy/skahsCgYEA0d/t
# Id1ND8bX4ZXyg4DPfJoIOca8VmMbjIl6xsPc4nuYKTDAnUK5k00gJqGs7+pHJEdD
# xw7s5hk0F0dxQjMe8S+eZv4AuwoepZJ+uAJ05KLVLkBa0yLrcg6xEYX56fbPhy3r
# fTBly/HBKcWT/abNaVZSP6qgDwNuK3/AJmEugpcCgYEA41DEOcMJnqKkyDUzX+Un
# hI63eVo/DNH5DUxcgzEi9pODgTUhwgzfkJly7lAdmiqp/8Rm2lhcPaDgjaM8PonX
# I5R4vKTWUyMgva9GA1fLfBhhnwFiP1JwZne6AiEnFxJPhulyydW1FsuN8AwnjF5E
# XG2o10ctml8LeTbtmj+tlhsCgYB9Rv11yXPGhxs2PRuWA73W0ts2Ibsqld5L9YSk
# QSYIy134uHFBbiL4GoGmjbt9OotczG1Y1T/z2feOLccdjQZbUeFr+RLWkyPYEaoy
# jMTZ9ZjrEt8kSSPh4YMwwph7YChguLho8grRwm1bUeUU9AyJZE2UU3VXgOSycn9w
# aXIp4QKBgQChttQbfh7y3cpVdXcIdGvp3zjKaInsswIEwEmYWq14WZCnocfGZ2Xj
# iPACxug8XTixYmSVMeGfGhsehRcxWHrzmxKEuadB8yI/yKnXR0IfHvY+IZHUhaYH
# 421G9aSN4nPCtWScs6K1YqvQQzKaC55OLpG5ca0bDPu/FYQXZNE+Ng==
# -----END RSA PRIVATE KEY-----
#     '';
#   };

}
