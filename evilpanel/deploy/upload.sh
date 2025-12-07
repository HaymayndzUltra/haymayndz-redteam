#!/bin/bash
# ============================================================
# EvilPanel Upload Script
# Run from LOCAL machine to upload files to VPS
# ============================================================
#
# Usage:
#   chmod +x upload.sh
#   ./upload.sh
#
# ============================================================

VPS_IP="206.189.92.6"
VPS_USER="root"
SSH_KEY="/home/haymayndz/.ssh/id_ed25519_maxphisher"
LOCAL_EVILPANEL="/home/haymayndz/maxphisher2-clean/evilpanel"
REMOTE_DIR="/opt/evilpanel"

# SSH options with key
SSH_OPTS="-i ${SSH_KEY} -o StrictHostKeyChecking=no"

echo "============================================================"
echo "  EvilPanel Upload Script"
echo "  Target: ${VPS_USER}@${VPS_IP}:${REMOTE_DIR}"
echo "============================================================"
echo ""

# Create remote directory structure
echo "[1/4] Creating remote directories..."
ssh ${SSH_OPTS} ${VPS_USER}@${VPS_IP} "mkdir -p ${REMOTE_DIR}/{core,data,certs,logs,database,deploy,phishlets,config}"

# Upload evilpanel files (excluding cache and venv)
echo "[2/4] Uploading EvilPanel files..."
rsync -avz --progress \
    -e "ssh ${SSH_OPTS}" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='*.egg-info' \
    --exclude='dashboard/frontend/node_modules' \
    ${LOCAL_EVILPANEL}/ \
    ${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/

# Set permissions
echo "[3/4] Setting permissions..."
ssh ${SSH_OPTS} ${VPS_USER}@${VPS_IP} "chmod +x ${REMOTE_DIR}/run.py ${REMOTE_DIR}/deploy/*.sh"

# Verify upload
echo "[4/4] Verifying upload..."
ssh ${SSH_OPTS} ${VPS_USER}@${VPS_IP} "ls -la ${REMOTE_DIR}/"

echo ""
echo "============================================================"
echo "  Upload Complete!"
echo "============================================================"
echo ""
echo "Next steps on VPS:"
echo "  1. SSH to VPS: ssh ${VPS_USER}@${VPS_IP}"
echo "  2. Run deployment: cd ${REMOTE_DIR}/deploy && ./deploy.sh"
echo "  3. Verify: ./verify.sh"
echo ""
