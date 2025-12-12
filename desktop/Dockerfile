# Ubuntu 24.04 Desktop with KDE Plasma (Kubuntu) for Autonomous Agent
# ====================================================================
# Full-featured KDE desktop with VS Code, Firefox, and development tools

FROM ubuntu:24.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# VNC Configuration
ENV VNC_RESOLUTION=1920x1080
ENV VNC_COL_DEPTH=24
ENV DISPLAY=:1

# Agent Configuration
ENV AGENT_HEADLESS=false
ENV WORKSPACE=/workspace

# ============================================================================
# KDE Plasma Desktop + Essential Packages
# ============================================================================
RUN apt-get update && apt-get install -y \
    # KDE Plasma Desktop (lighter than full kubuntu-desktop)
    plasma-desktop \
    sddm \
    konsole \
    dolphin \
    kate \
    kde-spectacle \
    # Essential X11/VNC
    xorg \
    dbus-x11 \
    x11-xserver-utils \
    tigervnc-standalone-server \
    tigervnc-common \
    # Web-based VNC
    novnc \
    websockify \
    # Firefox Browser
    firefox \
    # Python
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    # Dev tools
    git \
    curl \
    wget \
    gnupg \
    software-properties-common \
    # Utilities
    jq \
    unzip \
    nano \
    vim \
    htop \
    supervisor \
    # Browser dependencies for Puppeteer
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
    libasound2t64 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    fonts-noto \
    xdg-utils \
    ca-certificates \
    # VS Code dependencies
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
# Puppeteer (for headless browser automation)
# ============================================================================
RUN npm install -g puppeteer

# Set Firefox as fallback for Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/firefox
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# ============================================================================
# Create agent user
# ============================================================================
RUN useradd -m -s /bin/bash agent \
    && echo "agent:agent" | chpasswd \
    && usermod -aG sudo agent

# ============================================================================
# VNC Setup for KDE
# ============================================================================
RUN mkdir -p /home/agent/.vnc \
    && chown -R agent:agent /home/agent/.vnc

# VNC startup script for KDE Plasma
RUN echo '#!/bin/bash' > /home/agent/.vnc/xstartup && \
    echo 'unset SESSION_MANAGER' >> /home/agent/.vnc/xstartup && \
    echo 'unset DBUS_SESSION_BUS_ADDRESS' >> /home/agent/.vnc/xstartup && \
    echo 'export XDG_SESSION_TYPE=x11' >> /home/agent/.vnc/xstartup && \
    echo 'export XDG_RUNTIME_DIR=/run/user/$(id -u)' >> /home/agent/.vnc/xstartup && \
    echo 'dbus-launch --exit-with-session startplasma-x11' >> /home/agent/.vnc/xstartup && \
    chmod +x /home/agent/.vnc/xstartup && \
    chown agent:agent /home/agent/.vnc/xstartup

# Create runtime directory for agent user
RUN mkdir -p /run/user/1000 && chown agent:agent /run/user/1000

# ============================================================================
# noVNC Setup
# ============================================================================
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true

# ============================================================================
# Agent Setup
# ============================================================================
WORKDIR /app

# Copy agent requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

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
