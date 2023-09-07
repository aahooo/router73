#!/opt/homebrew/bin//python3

import sys
import yaml
import os
import os.path

import pywgkey


help = f"""Renderer
  Usage: { os.path.relpath(__file__) } <config_file>
"""


def set_defaults(config):
  if "chisel_fingerprint" not in config["ingress"] or "chisel_fingerprint_hash" not in config["ingress"]:
    config["ingress"]["chisel_fingerprint"] = "hello"
    config["ingress"]["chisel_fingerprint_hash"] = "70JeX90JT3uEA023/yZXx+cgpaE+je1T0A9TYM2OtCo="

  if "tls_crt" not in config["ingress"] or "tls_key" not in config["ingress"]:
    config["ingress"]["tls_crt"] = f"""{ config["ingress"]["https_domain"] }.crt.pem"""
    config["ingress"]["tls_key"] = f"""{ config["ingress"]["https_domain"] }.key.pem"""

  if "https_listen_ip" not in config["ingress"]:
    config["ingress"]["https_listen_ip"] = config["ingress"]["public_ip"]

  if "ovpn_listen_ip" not in config["ingress"]:
    config["ingress"]["ovpn_listen_ip"] = config["ingress"]["public_ip"]

  if "grafana_listen_ip" not in config["ingress"]:
    config["ingress"]["grafana_listen_ip"] = config["ingress"]["public_ip"]
  
  if "admin_ui_listen_ip" not in config["ingress"]:
    config["ingress"]["admin_ui_listen_ip"] = config["ingress"]["public_ip"]

  if "tunnels" not in config["egress"]:
    config["egress"]["tunnels"] = [
      {"name": "tunl1", "ip": "10.9.0.1", "peer_ip": "10.9.0.2", "forward_port": "50001"},
      {"name": "tunl2", "ip": "10.9.0.3", "peer_ip": "10.9.0.4", "forward_port": "50002"},
      {"name": "tunl3", "ip": "10.9.0.5", "peer_ip": "10.9.0.6", "forward_port": "50003"}
    ]
  for i in range(3):
    server_key, peer_key = pywgkey.WgKey(), pywgkey.WgKey()
    config["egress"]["tunnels"][i]["key"] = server_key.privkey
    config["egress"]["tunnels"][i]["pubkey"] = server_key.pubkey
    config["egress"]["tunnels"][i]["peer_key"] = peer_key.privkey
    config["egress"]["tunnels"][i]["peer_pubkey"] = peer_key.pubkey

  return config

def generate_egress(config):
  header = f"""version: "3.3"
services:
  autoheal:
    restart: always
    image: willfarrell/autoheal
    environment:
      - AUTOHEAL_CONTAINER_LABEL=all
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

"""

  prometheus_service = """  prometheus:
      image: prom/prometheus:v2.44.0
      command:
      - /bin/sh
      - -c
      - "cat > /etc/prometheus/prometheus.yaml <<EOF
          global:
            scrape_interval: 15s
            evaluation_interval: 15s

          scrape_configs:
          - job_name: \\"prometheus\\"
            static_configs:
            - targets: [\\"localhost:9090\\"]

          - job_name: \\"egress_wireguard\\"
            static_configs:
            - targets:
"""
  for tunnel in config["egress"]["tunnels"]:
    prometheus_service += f"""              - wg-{ tunnel["name"] }\n"""
  prometheus_service += f"""        EOF
        && /bin/prometheus \
            --config.file /etc/prometheus/prometheus.yaml \
            --storage.tsdb.path /prometheus \
            --web.console.templates /etc/prometheus/consoles \
            --web.console.libraries /etc/prometheus/console_libraries \
            --web.listen-address :9090"
      ports:
        - "{config["egress"]["public_ip"]}:9090:{config["egress"]["metrics_port"]}"
      volumes:
        - type: bind
          source: ./prometheus
          target: /etc/prometheus

"""

  wg_services = ""
  for tunnel in config["egress"]["tunnels"]:
    wg_services += f"""  wg-{ tunnel["name"] }:
      build:
        context: ./
        dockerfile: ./build/Dockerfile
      restart: "always"
      environment:
        CHISEL_ENDPOINT: https://{ config["ingress"]["https_domain"] }
        CHISEL_FINGERPRINT: { config["ingress"]["chisel_fingerprint_hash"] }
        PEER_ADDR: { config["ingress"]["public_ip"] }
        PEER_PORT: { int(tunnel["forward_port"]) }
        WG_ADDR: { tunnel["ip"] }
        WG_KEY: { tunnel["key"] }
        PEER_WG_ADDR: { tunnel["peer_ip"] }
        PEER_PUBKEY: { tunnel["peer_pubkey"] }
      volumes:
        - type: bind
          source: ./wireguard/wg.conf.tmpl
          target: /etc/wireguard/wg.conf.tmpl
          read_only: true
        - type: bind
          source: ./bird/bird.conf.tmpl
          target: /etc/bird/bird.conf.tmpl
          read_only: true
      privileged: true
      healthcheck:
        test: ["CMD", "ping", "-c", "1", "-w", "2", "{ tunnel["peer_ip"] }"]
        interval: 15s
        timeout: 5s
        retries: 3
        start_period: 30s

"""
  return header+prometheus_service+wg_services

def generate_ingress(config):
  header = """version: "3.3"
services:
  autoheal:
    restart: always
    image: willfarrell/autoheal
    environment:
      - AUTOHEAL_CONTAINER_LABEL=all
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

"""
  chisel_service = f"""  chisel:
    image: jpillora/chisel:1.7.7
    command:
      - server
      - -p
      - "443"
      - --tls-key
      - /keys/{ config["ingress"]["tls_key"] }
      - --tls-cert
      - /keys/{ config["ingress"]["tls_crt"] }
      - --key
      - { config["ingress"]["chisel_fingerprint"] }
      - --reverse
      - --backend
      - http://admin-ui:80/
    volumes:
      - type: bind
        source: ./configs/keys
        target: /keys
    ports:
      - "{ config["ingress"]["https_listen_ip"]}:443:{config["ingress"]["https_listen_port"] }"

"""
  admin_ui_service = f"""  admin-ui:
    build:
      context: ./
      dockerfile: ./build/admin-ui/Dockerfile
    command:
      - /bin/bash
      - -c
      - " ./db.py { config["ingress"]["admin_ui_username"] } \
                  { config["ingress"]["admin_ui_password"] } && \
            gunicorn --bind 0.0.0.0:80 --log-level info \
              --access-logfile /logs/access --error-logfile /logs/error manage:app"
    volumes:
      - type: bind
        source: ./db
        target: /data
      - type: bind
        source: ./logs
        target: /logs
      - type: bind
        source: ./configs/ovpn
        target: /configs
        read_only: true
    ports:
      - "{ config["ingress"]["admin_ui_listen_ip"]}:8088:{config["ingress"]["admin_ui_listen_port"] }"


"""
  openvpn_service = f"""  ovpn:
    build:
      context: ./
      dockerfile: ./build/ovpn/Dockerfile
    restart: "always"
    environment:
      EXCLUDE_CIDRS_FILE: "/opt/exclude-ranges.txt"
      WG_KEY_A: "{ config["egress"]["tunnels"][0]["peer_key"] }"
      WG_KEY_B: "{ config["egress"]["tunnels"][1]["peer_key"] }"
      WG_KEY_C: "{ config["egress"]["tunnels"][2]["peer_key"] }"

      WG_SERVER_PUBKEY_A: "{ config["egress"]["tunnels"][0]["pubkey"] }"
      WG_SERVER_PUBKEY_B: "{ config["egress"]["tunnels"][1]["pubkey"] }"
      WG_SERVER_PUBKEY_C: "{ config["egress"]["tunnels"][2]["pubkey"] }"

      WG_ADDR_A: "{ config["egress"]["tunnels"][0]["peer_ip"] }"
      WG_ADDR_B: "{ config["egress"]["tunnels"][1]["peer_ip"] }"
      WG_ADDR_C: "{ config["egress"]["tunnels"][2]["peer_ip"] }"

      WG_SRV_ADDR_A: "{ config["egress"]["tunnels"][0]["ip"] }"
      WG_SRV_ADDR_B: "{ config["egress"]["tunnels"][1]["ip"] }"
      WG_SRV_ADDR_C: "{ config["egress"]["tunnels"][2]["ip"] }"

      WG_INTERFACE_A: "wg1"
      WG_INTERFACE_B: "wg2"
      WG_INTERFACE_C: "wg3"

      WG_PORT_A: "{ config["egress"]["tunnels"][0]["forward_port"] }"
      WG_PORT_B: "{ config["egress"]["tunnels"][1]["forward_port"] }"
      WG_PORT_C: "{ config["egress"]["tunnels"][2]["forward_port"] }"
    depends_on:
      - admin-ui
    volumes:
      - type: bind
        source: ./configs/ovpn
        target: /etc/openvpn/server
      - type: bind
        source: ./configs/wireguard/wg.conf.tmpl
        target: /etc/wireguard/wg.conf.tmpl
        read_only: true
      - type: bind
        source: ./configs/bird/bird.conf.tmpl
        target: /etc/bird/bird.conf.tmpl
      - type: bind
        source: ./build/ovpn/exclude-ranges.txt
        target: /opt/exclude-ranges.txt
        read_only: true
    ports:
      - "{ config["ingress"]["ovpn_listen_ip"] }:444:{ config["ingress"]["ovpn_listen_port"] }"
    privileged: true

"""

  prometheus_service = f"""  prometheus:
      image: prom/prometheus:v2.44.0
      command:
      - /bin/sh
      - -c
      - "cat > /etc/prometheus/prometheus.yaml <<EOF
          global:
            scrape_interval: 15s
            evaluation_interval: 15s

          scrape_configs:
          - job_name: \\"prometheus\\"
            static_configs:
            - targets: [\\"localhost:9090\\"]

          - job_name: \\"openvpn\\"
            dns_sd_configs:
            - names:
              - ovpn
              type: A
              port: 9176

          - job_name: \\"wireguard\\"
            scrape_interval: 15s
            honor_labels: true
            metrics_path: '/federate'
            params:
              'match[]':
                - '{{job=\\"egress_wireguard\\"}}'
            static_configs:
            - targets:
              - '{ config["egress"]["public_ip"] }:{config["egress"]["metrics_port"] }'
        EOF
        && /bin/prometheus
          --config.file /etc/prometheus/prometheus.yaml \
          --storage.tsdb.path /prometheus \
          --web.console.templates /etc/prometheus/consoles \
          --web.console.libraries /etc/prometheus/console_libraries \
          --web.listen-address :9090"
      volumes:
        - type: bind
          source: ./prometheus
          target: /etc/prometheus

"""

  grafana_service = f"""  grafana:
    image: grafana/grafana:main-ubuntu
    user: root
    depends_on:
      - prometheus
    volumes:
      - type: bind
        source: ./grafana
        target: /var/lib/grafana
    ports:
      - "{ config["ingress"]["grafana_listen_ip"] }:34543:{ config["ingress"]["grafana_listen_port"] }"

"""
  return header+chisel_service+admin_ui_service+openvpn_service+prometheus_service+grafana_service

def main():
  if len(sys.argv) < 2:
    config_filename = "config.yaml"
    print(help)
    sys.exit(0)
  else:
    config_filename = sys.argv[1]

  with open(config_filename, "r") as config_file:
    print(f"Loading config file from `{config_filename}`")
    config = yaml.safe_load(config_file)

  config = set_defaults(config)

  os.system(f"""./easyrsa_generate.sh { config["ingress"]["https_domain"] }""")

  with open("ingress/docker-compose.yaml", "w") as file:
    print(f"Writing ingress compose file to `ingress/docker-compose.yaml`")
    file.write(generate_ingress(config))
  with open("egress/docker-compose.yaml", "w") as file:
    print(f"Writing egress compose file to `egress/docker-compose.yaml`")
    file.write(generate_egress(config))

if __name__ == "__main__":
  main()
