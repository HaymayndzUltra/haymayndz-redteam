#!/bin/bash
# SSH connection and directory tree retrieval script

echo "Connecting to remote server..."
ssh -i /home/haymayndz/.ssh/id_ed25519_maxphisher -o StrictHostKeyChecking=no root@152.42.229.105 << 'REMOTE_SCRIPT'
cd /
echo "=== Directory Tree Structure ==="
echo ""

# Try tree command first
if command -v tree &> /dev/null; then
    echo "Using 'tree' command:"
    tree -L 4 -d 2>/dev/null || tree -L 3 -d
else
    echo "Using 'find' command (tree not available):"
    find / -maxdepth 4 -type d 2>/dev/null | \
        grep -vE '^/(proc|sys|dev|run|tmp|var/tmp)' | \
        sort | \
        sed 's|^/||' | \
        awk '{
            depth = gsub(/\//, "/", $0);
            indent = "";
            for (i = 0; i < depth; i++) indent = indent "  ";
            print indent $0
        }' | head -200
fi

echo ""
echo "=== Key Directories ==="
ls -la / | grep "^d" | awk '{print $9}' | grep -v "^\.$"
REMOTE_SCRIPT

echo ""
echo "Script completed."

