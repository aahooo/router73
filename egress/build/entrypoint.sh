#!/bin/bash

set -o errexit -o pipefail -o nounset

: ${GATEWAY_ADDR:="$(ip r get 8.8.8.8 | grep 8.8.8.8 | cut -d' ' -f3)"}
: ${SRC_ADDR:="$(ip r get "${GATEWAY_ADDR}" | grep "${GATEWAY_ADDR}" | cut -d' ' -f5)"}


main() {
  sysctl -w net.ipv4.ip_forward=1

  create_wg_config
  create_bird_config

  wg-quick up wg0

  bird -c /etc/bird/bird.conf

  /usr/local/bin/wg-exporter &

  exec /usr/local/bin/chisel client --tls-skip-verify \
    --fingerprint "${CHISEL_FINGERPRINT}" "${CHISEL_ENDPOINT}" \
    "R:${PEER_ADDR}:${PEER_PORT}:127.0.0.1:51820/udp"
}

create_wg_config() {
  RENDERED=$(cat /etc/wireguard/wg.conf.tmpl)
  RENDERED=${RENDERED//#WG_ADDR/$WG_ADDR}
  RENDERED=${RENDERED//#WG_KEY/$WG_KEY}
  RENDERED=${RENDERED//#PEER_WG_ADDR/$PEER_WG_ADDR}
  RENDERED=${RENDERED//#PEER_PUBKEY/$PEER_PUBKEY}
  RENDERED=${RENDERED//#SRC_ADDR/$SRC_ADDR}

  echo "${RENDERED}" > /etc/wireguard/wg0.conf

}

create_bird_config() {
  RENDERED=$(cat /etc/bird/bird.conf.tmpl)
  RENDERED=${RENDERED//#WG_ADDR/$WG_ADDR}
  RENDERED=${RENDERED//#PEER_WG_ADDR/$PEER_WG_ADDR}
  RENDERED=${RENDERED//#SRC_ADDR/$SRC_ADDR}

  echo "${RENDERED}" > /etc/bird/bird.conf

}

if [[ "$1" == "main" ]]; then
  main
else
  exec "$@"
fi
