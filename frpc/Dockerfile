FROM alpine:3.23

ARG FRP_VERSION=0.62.0
ARG TARGETARCH=amd64

RUN apk add --no-cache curl ca-certificates && \
    curl -fsSL \
      "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${TARGETARCH}.tar.gz" \
      -o /tmp/frp.tar.gz && \
    tar -xzf /tmp/frp.tar.gz -C /tmp && \
    mv /tmp/frp_${FRP_VERSION}_linux_${TARGETARCH}/frpc /usr/local/bin/frpc && \
    chmod +x /usr/local/bin/frpc && \
    rm -rf /tmp/frp* && \
    apk del curl

# Non-root user
RUN adduser -D -u 1000 frp
USER frp

ENTRYPOINT ["/usr/local/bin/frpc"]
CMD ["-c", "/etc/frp/frpc.toml"]
