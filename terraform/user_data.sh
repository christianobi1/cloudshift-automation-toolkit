#!/bin/bash

set -euxo pipefail

# Log everything for troubleshooting
exec > >(tee /var/log/user-data.log | logger -t cloudshift-user-data) 2>&1

echo "Starting Cloudshift Store provisioning..."

# ---------------------------------------------
# 1. Update packages
# ---------------------------------------------
dnf update -y

# ---------------------------------------------
# 2. Install Docker and Git
# ---------------------------------------------
dnf install -y docker git

# ---------------------------------------------
# 3. Start Docker
# ---------------------------------------------
systemctl enable docker
systemctl start docker

# Wait until Docker is ready
until docker info >/dev/null 2>&1; do
echo "waiting for Docker to start..."
sleep 2
done

echo "Docker is running."

# ---------------------------------------------
# 4. Allow ec2-user to use Docker
# ---------------------------------------------
usermod -aG docker ec2-user

# ---------------------------------------------
# 5. Install Docker Compose
# ---------------------------------------------
mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL \
  https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Verify Docker Compose
docker compose version

# ---------------------------------------------
# 6. Clone monitoring branch
# ---------------------------------------------

rm -rf /home/ec2-user/app

git clone \
-b main \
--single-branch \
https://github.com/christianobi1/cloudshift-automation-toolkit.git \
/home/ec2-user/app

# ----------------------------------------------
# 7. Move into application directory
# ----------------------------------------------
cd /home/ec2-user/app   

# ----------------------------------------------
# 8. Verify required files
# ----------------------------------------------
test -f docker-compose.yml
test -f prometheus.yml
test -f Dockerfile

echo "Required application files found"

# -----------------------------------------------
# 9. Start everything
# -----------------------------------------------
docker compose up -d --build

# -----------------------------------------------
# 10. Show running containers
# -----------------------------------------------
docker compose ps

echo "-------------------------------------------"
echo "Cloudshift Store provisioning completed!"
echo "Cloudshift Store: http://EC2_PUBLIC_IP"
echo "Prometheus: http://EC2_PUBLIC_IP:9090"
echo "Grafana: http://EC2_PUBLIC_IP:3000"
echo "-------------------------------------------"