FROM rust:slim-buster as builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /

RUN apt-get update && apt-get install -yqq --no-install-recommends git \
 && git clone https://github.com/MindFlavor/prometheus_wireguard_exporter.git

WORKDIR /prometheus_wireguard_exporter

RUN cargo install --path .

FROM ubuntu:20.04

ARG ARCH=amd64
ARG OS=linux
ARG CHISEL_VERSION=1.7.7

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -yqq --no-install-recommends \ 
      ca-certificates iptables mtr curl vim wireguard-tools bird iproute2 iputils-ping \
 && mkdir /run/bird \
 && curl -SL "https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_${OS}_${ARCH}.gz" \
 |  gzip -d > /usr/local/bin/chisel \
 && chmod +x /usr/local/bin/chisel

COPY --from=builder /prometheus_wireguard_exporter/target/release/prometheus_wireguard_exporter /usr/local/bin/wg-exporter
RUN chmod +x /usr/local/bin/wg-exporter

COPY build/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "main" ]
