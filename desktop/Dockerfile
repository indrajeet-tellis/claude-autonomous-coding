# Ubuntu Desktop with VNC for Autonomous Agent
# ==============================================
# Includes Chrome, VS Code, and development tools

FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# VNC Configuration
ENV VNC_RESOLUTION=1920x1080
ENV VNC_COL_DEPTH=24
# No VNC password - open access
ENV DISPLAY=:1

# Agent Configuration
ENV AGENT_HEADLESS=false
ENV WORKSPACE=/workspace

# ============================================================================
# System Dependencies + Chromium (ARM64 compatible)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Minimal desktop environment
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    x11-xserver-utils \
    # VNC
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \
    # Web-based VNC
    novnc \
    websockify \
    # Python
    python3 \
    python3-pip \
    python3-venv \
    # Dev tools
    git \
    curl \
    wget \
    gnupg \
    # Utilities
    jq \
    unzip \
    nano \
    supervisor \
    # Chromium (works on ARM64)
    chromium-browser \
    # Chromium dependencies
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    xdg-utils \
    ca-certificates \
    # Additional dependencies for VS Code
    libsecret-1-0 \
    libxss1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ============================================================================
# Node.js 20 LTS
# ============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chromium path for Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# ============================================================================
# Visual Studio Code
# ============================================================================
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list \
    && apt-get update \
    && apt-get install -y code \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Puppeteer
# ============================================================================
RUN npm install -g puppeteer


# ============================================================================
# Create agent user
# ============================================================================
RUN useradd -m -s /bin/bash agent \
    && echo "agent:agent" | chpasswd

# ============================================================================
# VNC Setup (no password)
# ============================================================================
RUN mkdir -p /home/agent/.vnc \
    && chown -R agent:agent /home/agent/.vnc

# VNC startup script - must keep running in foreground
RUN echo '#!/bin/bash' > /home/agent/.vnc/xstartup && \
    echo 'unset SESSION_MANAGER' >> /home/agent/.vnc/xstartup && \
    echo 'unset DBUS_SESSION_BUS_ADDRESS' >> /home/agent/.vnc/xstartup && \
    echo 'export XKL_XMODMAP_DISABLE=1' >> /home/agent/.vnc/xstartup && \
    echo '[ -r $HOME/.Xresources ] && xrdb $HOME/.Xresources' >> /home/agent/.vnc/xstartup && \
    echo 'exec startxfce4' >> /home/agent/.vnc/xstartup && \
    chmod +x /home/agent/.vnc/xstartup && \
    chown agent:agent /home/agent/.vnc/xstartup

# ============================================================================
# noVNC Setup
# ============================================================================
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# ============================================================================
# Agent Setup
# ============================================================================
WORKDIR /app

# Copy agent requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent/ ./agent/
COPY prompts.py client.py ./

# Create workspace
RUN mkdir -p /workspace /app/screenshots \
    && chown -R agent:agent /workspace /app

# ============================================================================
# Supervisor Configuration
# ============================================================================
COPY desktop/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ============================================================================
# Startup Script  
# ============================================================================
COPY desktop/startup.sh /startup.sh
RUN chmod +x /startup.sh

# ============================================================================
# Ports
# ============================================================================
EXPOSE 5901 6080 3000 5000 8000 8080

# ============================================================================
# Run
# ============================================================================
CMD ["/startup.sh"]
