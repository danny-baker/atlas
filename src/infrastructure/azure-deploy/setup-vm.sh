#!/bin/bash

# This is an executable shell script to do the initial setup on a VM.  

# ===DOCKER===

# https://docs.docker.com/engine/install/ubuntu/
sudo apt-get update
echo "### Installing Docker..."

# packages
sudo apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

# add docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# verify 
sudo apt-key fingerprint 0EBFCD88

# setup stable repository
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

# install docker engine
sudo apt-get -y install docker-ce docker-ce-cli containerd.io

# ===DOCKER-COMPOSE===

# https://docs.docker.com/compose/install/

echo "### Installing docker-compose..."

# download current release
sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# apply executable permissions to binary
sudo chmod +x /usr/local/bin/docker-compose

# check version to see if install ok
docker-compose --version

# give user root access to docker prevent all this sudo nonsense (logout required)
sudo usermod -aG docker dan

# ===TAILSCALE VPN===
echo "### Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey SECRET_TAILSCALE_AUTHKEY


