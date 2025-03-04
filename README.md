# Music Streaming Private IaaS

## Run locally

docker compose up

## Deploy with k3s + tailscale

Configure Tailscale networking with k3s first: https://docs.k3s.io/networking/distributed-multicloud#integration-with-the-tailscale-vpn-provider-experimental
Then:

sudo kubectl apply -f k8s/*

