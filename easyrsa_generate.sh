#!/bin/bash

if [[ $# < 1 ]]; then exit 1; fi
DOMAIN_NAME="$1"

curl -SL https://github.com/OpenVPN/easy-rsa/releases/download/v3.1.5/EasyRSA-3.1.5.tgz | tar -zx
mv EasyRSA-3.1.5 EasyRSA

EasyRSA/easyrsa init-pki
echo "ca" | EasyRSA/easyrsa build-ca nopass
yes "yes" 2> /dev/null | EasyRSA/easyrsa build-server-full server nopass
EasyRSA/easyrsa gen-dh
yes "yes" 2> /dev/null | EasyRSA/easyrsa build-server-full "${DOMAIN_NAME}" nopass

cp pki/ca.crt ingress/configs/ovpn/ca.crt
cp pki/issued/server.crt ingress/configs/ovpn/server.crt
cp pki/private/server.key ingress/configs/ovpn/server.key
cp pki/dh.pem ingress/configs/ovpn/dh.pem
cp pki/issued/${DOMAIN_NAME}.crt ingress/configs/keys/${DOMAIN_NAME}.crt.pem
cp pki/private/${DOMAIN_NAME}.key ingress/configs/keys/${DOMAIN_NAME}.key.pem

rm -rf EasyRSA pki
