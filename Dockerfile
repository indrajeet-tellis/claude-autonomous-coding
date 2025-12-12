# Docker Autonomous Agent base image
FROM ubuntu:22.04

# Prevent timezone prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python
    python3.11 \
    python3.11-venv \
    python3-pip \
    # Node.js prerequisites
    curl \
    gnupg \
    # Build tools
    build-essential \
    git \
    # Utilities
    jq \
    wget \
    unzip \
    # Chrome dependencies
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
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome path for Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Install Puppeteer globally
RUN npm install -g puppeteer puppeteer-cli

# Create app directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Create workspace directory
RUN mkdir -p /workspace

# Set workspace as volume
VOLUME /workspace

# Set working directory to workspace for agent operations
WORKDIR /workspace

# Default command runs the agent
CMD ["python3", "/app/agent.py"]
