#!/bin/bash

set -o errexit -o pipefail -o nounset

: ${GATEWAY_IP:="$(ip r get 8.8.8.8 | grep 8.8.8.8 | cut -d' ' -f3)"}
: ${SRC_IP:="$(ip r get "${GATEWAY_IP}" | grep "${GATEWAY_IP}" | cut -d' ' -f5)"}
: ${GATEWAY_INTERFACE:="$(ip a | grep "${SRC_IP}" | awk '{print $7}')"}

: ${OVPN_NET:="10.8.0.0/16"}
: ${METRICS_PORT:="9176"}

main() {
  ipset create exclude hash:net

  if [[ -e "${EXCLUDE_CIDRS_FILE}" ]]; then
    for block in $(cat "${EXCLUDE_CIDRS_FILE}" | grep -v "#"); do
      ipset add exclude "${block}"
      ip -4 route add "${block}" via "${GATEWAY_IP}" dev "${GATEWAY_INTERFACE}"
    done
  fi

  ip -4 route del default via "${GATEWAY_IP}" dev "${GATEWAY_INTERFACE}" || true

  create_wg_config
  create_bird_config

  wg-quick up ${WG_INTERFACE_A}
  wg-quick up ${WG_INTERFACE_B}
  wg-quick up ${WG_INTERFACE_C}

  bird -c /etc/bird/bird.conf

  sysctl -w net.ipv4.fib_multipath_hash_policy=1

  iptables -A FORWARD -s "${OVPN_NET}" -j ACCEPT
  iptables -t nat -A POSTROUTING -s "${OVPN_NET}" -m set --match-set exclude dst -j SNAT --to-source "${SRC_IP}"
  iptables -t nat -A POSTROUTING -s "${OVPN_NET}" ! -d "${OVPN_NET}" -j MASQUERADE

  openvpn_exporter -openvpn.status_paths /var/log/openvpn/openvpn-status.log -web.listen-address ":${METRICS_PORT}" &

  exec /usr/sbin/openvpn --suppress-timestamps --cd /etc/openvpn/server/ --config /etc/openvpn/server/server.conf
}

create_wg_config() {
  RENDERED=$(cat /etc/wireguard/wg.conf.tmpl)
  RENDERED=${RENDERED//#GATEWAY_IP/$GATEWAY_IP}
  RENDERED=${RENDERED//#WG_KEY/$WG_KEY_A}
  RENDERED=${RENDERED//#WG_SERVER_PUBKEY/$WG_SERVER_PUBKEY_A}

  RENDERED=${RENDERED//#WG_INTERFACE/$WG_INTERFACE_A}
  RENDERED=${RENDERED//#WG_ADDR/$WG_ADDR_A}
  RENDERED=${RENDERED//#WG_SRV_ADDR/$WG_SRV_ADDR_A}
  RENDERED=${RENDERED//#WG_PORT/$WG_PORT_A}

  echo "${RENDERED}" > /etc/wireguard/wg1.conf

  RENDERED=$(cat /etc/wireguard/wg.conf.tmpl)
  RENDERED=${RENDERED//#GATEWAY_IP/$GATEWAY_IP}
  RENDERED=${RENDERED//#WG_KEY/$WG_KEY_B}
  RENDERED=${RENDERED//#WG_SERVER_PUBKEY/$WG_SERVER_PUBKEY_B}

  RENDERED=${RENDERED//#WG_INTERFACE/$WG_INTERFACE_B}
  RENDERED=${RENDERED//#WG_ADDR/$WG_ADDR_B}
  RENDERED=${RENDERED//#WG_SRV_ADDR/$WG_SRV_ADDR_B}
  RENDERED=${RENDERED//#WG_PORT/$WG_PORT_B}

  echo "${RENDERED}" > /etc/wireguard/wg2.conf

  RENDERED=$(cat /etc/wireguard/wg.conf.tmpl)
  RENDERED=${RENDERED//#GATEWAY_IP/$GATEWAY_IP}
  RENDERED=${RENDERED//#WG_KEY/$WG_KEY_C}
  RENDERED=${RENDERED//#WG_SERVER_PUBKEY/$WG_SERVER_PUBKEY_C}

  RENDERED=${RENDERED//#WG_INTERFACE/$WG_INTERFACE_C}
  RENDERED=${RENDERED//#WG_ADDR/$WG_ADDR_C}
  RENDERED=${RENDERED//#WG_SRV_ADDR/$WG_SRV_ADDR_C}
  RENDERED=${RENDERED//#WG_PORT/$WG_PORT_C}

  echo "${RENDERED}" > /etc/wireguard/wg3.conf

}

create_bird_config() {
  RENDERED=$(cat /etc/bird/bird.conf.tmpl)
  RENDERED=${RENDERED//#SRC_IP/$SRC_IP}

  RENDERED=${RENDERED//#WG_ADDR_A/$WG_ADDR_A}
  RENDERED=${RENDERED//#WG_ADDR_B/$WG_ADDR_B}
  RENDERED=${RENDERED//#WG_ADDR_C/$WG_ADDR_C}

  RENDERED=${RENDERED//#WG_SRV_ADDR_A/$WG_SRV_ADDR_A}
  RENDERED=${RENDERED//#WG_SRV_ADDR_B/$WG_SRV_ADDR_B}
  RENDERED=${RENDERED//#WG_SRV_ADDR_C/$WG_SRV_ADDR_C}

  echo "${RENDERED}" > /etc/bird/bird.conf

}

if [[ "$1" == "main" ]]; then
  main
else
  exec "$@"
fi
