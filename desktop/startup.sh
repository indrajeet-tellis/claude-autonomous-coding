#!/bin/bash
# ============================================================================
# Desktop Startup Script
# ============================================================================

set -e

# Update VNC password if changed
if [ -n "$VNC_PASSWORD" ]; then
    echo "$VNC_PASSWORD" | vncpasswd -f > /home/agent/.vnc/passwd
    chmod 600 /home/agent/.vnc/passwd
    chown agent:agent /home/agent/.vnc/passwd
fi

# Set resolution
export VNC_RESOLUTION=${VNC_RESOLUTION:-1920x1080}

# Start supervisor (manages VNC, noVNC, and agent)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
