# Router 73

## Introduction
Router 73 is a project designed to provide secure internet access to users in a restricted network. It was designed for lossy and highly restricted networks with performance and scalability in mind.

## Design
Comming soon...

## How to use
To deploy this project, at minimum two servers are required. one inside the restricted network (aka ingress) and one outside of it (aka egress). The server inside the network handles client connections and the one outside forwards traffic to the internet.
### Configuration
A sample configuration file (config.yaml) is provided. The following configs need to be set in order to generate manifest files:
-   `egress.public_ip`:  Egress server public ip address.
-   `ingress.public_ip`:  Ingress server public ip address.
-   `ingress.https_domain`:  Domain name pointing to the ingress server through either dns lookup or any CDN.

The following configs could be changed or left as default depending on your specific needs:
-   `ingress.https_listen_port`:  The port on which ingress listens for `ingress.https_domain` connections. If traffic is transported via a CDN, origin forward port must be set to this value. Otherwise no further configuration is necessary.
-   `egress.metrics_port`: Egress server metrics port.
-   `ingress.ovpn_listen_port`:  The port on which ingress server accepts openvpn connections.
-   `ingress.grafana_listen_port`:  The port on which inress server serves the grafana service.
-   `ingress.admin_ui_username`: Username for administration panel.
-   `ingress.admin_ui_password`: Password for administration panel.

### Generating manifests
The requirements:
-   python3
-   python3-pip
-   pywgkey

Simply running `python3 generate.py config.yaml` generates keys and deployable manifests.

### Setting up the environment
The following packages must be installed on both ingress and egress servers:
-   docker
-   docker-compose
-   wireguard

Note: after installing wireguard, enable the kernel module by running `modprob wireguard`

### Deploy
Copy egress and ingress directories to the respective servers, then run `docker-compose up -d` in the directory where `docker-compose.yaml` exists on both servers. Health probes check th status of internal connections, so if `docker-compose ps` shows containers to be unhealthy, review your configurations and/or regenerate the manifests.
