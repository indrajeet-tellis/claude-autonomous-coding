#!/bin/bash
# ============================================================================
# Docker Autonomous Agent - Run Script
# ============================================================================
# 
# Usage:
#   ./run.sh                  # Run with default task.yaml in workspace
#   ./run.sh build           # Build/rebuild the Docker image
#   ./run.sh logs            # View agent logs
#   ./run.sh shell           # Open a shell in the container
#   ./run.sh stop            # Stop the agent
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check for .env file
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found${NC}"
        echo -e "Creating from .env.example..."
        
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${RED}Please edit .env and add your API key!${NC}"
            exit 1
        else
            echo -e "${RED}Error: .env.example not found${NC}"
            exit 1
        fi
    fi
}

# Create workspace directory if it doesn't exist
ensure_workspace() {
    mkdir -p workspace screenshots
    
    # Copy example task if workspace is empty
    if [ ! -f "workspace/task.yaml" ]; then
        echo -e "${CYAN}No task.yaml found in workspace.${NC}"
        echo -e "Copying example task..."
        cp examples/task.yaml workspace/task.yaml
        echo -e "${GREEN}Created workspace/task.yaml from example${NC}"
        echo -e "${YELLOW}Edit workspace/task.yaml to define your own task!${NC}"
    fi
}

# Build the Docker image
build() {
    echo -e "${CYAN}Building Docker image...${NC}"
    docker compose build
    echo -e "${GREEN}Build complete!${NC}"
}

# Run the agent
run() {
    check_env
    ensure_workspace
    
    echo -e "${CYAN}Starting autonomous agent...${NC}"
    echo -e "Workspace: ${SCRIPT_DIR}/workspace"
    echo -e "Screenshots: ${SCRIPT_DIR}/screenshots"
    echo ""
    
    docker compose up
}

# View logs
logs() {
    docker compose logs -f
}

# Open shell in container
shell() {
    docker compose exec agent /bin/bash
}

# Stop the agent
stop() {
    echo -e "${CYAN}Stopping agent...${NC}"
    docker compose down
    echo -e "${GREEN}Stopped.${NC}"
}

# Main
case "${1:-}" in
    build)
        build
        ;;
    logs)
        logs
        ;;
    shell)
        shell
        ;;
    stop)
        stop
        ;;
    "")
        run
        ;;
    *)
        echo "Usage: $0 {build|logs|shell|stop}"
        exit 1
        ;;
esac
