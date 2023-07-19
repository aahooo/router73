FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -yqq --no-install-recommends \ 
      openssl ca-certificates wget iptables iputils-ping dnsutils curl vim ipset openvpn python3-pip wireguard-tools bird \
 && python3 -m pip install requests \
 && mkdir /run/bird

COPY bin/openvpn_exporter /usr/bin/openvpn_exporter

COPY build/ovpn/exclude-ranges.txt /opt/exclude-ranges.txt

COPY build/ovpn/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "main" ]
