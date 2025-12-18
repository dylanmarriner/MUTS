#!/bin/bash

# Remote Server Setup Script
# This script runs on the remote Oracle Cloud server to complete the development environment setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Update and upgrade system
update_system() {
    log "Updating system packages..."
    apt-get update && apt-get upgrade -y
    log "System updated ✓"
}

# Install development tools
install_dev_tools() {
    log "Installing development tools..."
    
    # Install additional useful packages
    apt-get install -y \
        tree \
        unzip \
        zip \
        screen \
        tmux \
        neofetch \
        bat \
        exa \
        fd-find \
        ripgrep \
        fzf \
        jq \
        yq \
        httpie \
        speedtest-cli \
        net-tools \
        dnsutils \
        nmap \
        rsync
    
    log "Development tools installed ✓"
}

# Setup Python development environment
setup_python() {
    log "Setting up Python development environment..."
    
    # Install Python development tools
    pip3 install --upgrade pip
    pip3 install --user \
        virtualenv \
        pipenv \
        poetry \
        black \
        flake8 \
        pytest \
        mypy \
        pre-commit \
        jupyter \
        pandas \
        numpy \
        requests \
        python-dotenv
    
    # Create Python development directories
    mkdir -p /home/ubuntu/.local/bin
    echo 'export PATH="$PATH:/home/ubuntu/.local/bin"' >> /home/ubuntu/.bashrc
    
    log "Python environment setup completed ✓"
}

# Setup Node.js development environment
setup_nodejs() {
    log "Setting up Node.js development environment..."
    
    # Install global npm packages
    npm install -g \
        yarn \
        pnpm \
        typescript \
        ts-node \
        nodemon \
        pm2 \
        serve \
        http-server \
        @vercel/ncc \
        eslint \
        prettier \
        next \
        create-react-app \
        @angular/cli \
        vue-cli \
        vite \
        parcel
    
    # Create Node.js development directories
    mkdir -p /home/ubuntu/.npm-global
    npm config set prefix '/home/ubuntu/.npm-global'
    echo 'export PATH="/home/ubuntu/.npm-global/bin:$PATH"' >> /home/ubuntu/.bashrc
    
    log "Node.js environment setup completed ✓"
}

# Setup Docker
setup_docker() {
    log "Setting up Docker..."
    
    # Create docker group if not exists
    if ! getent group docker > /dev/null 2>&1; then
        groupadd docker
    fi
    
    # Add ubuntu user to docker group
    usermod -aG docker ubuntu
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    log "Docker setup completed ✓"
}

# Setup Git
setup_git() {
    log "Setting up Git configuration..."
    
    # Configure Git
    git config --global init.defaultBranch main
    git config --global pull.rebase false
    git config --global core.autocrlf input
    git config --global core.editor vim
    
    # Install useful Git tools
    curl -L https://github.com/extrawurst/gitui/releases/latest/download/gitui-linux-musl.tar.gz | tar xz -C /usr/local/bin gitui
    
    log "Git setup completed ✓"
}

# Setup Shell environment
setup_shell() {
    log "Setting up shell environment..."
    
    # Install Oh My Zsh if not already installed
    if [[ ! -d "/home/ubuntu/.oh-my-zsh" ]]; then
        sudo -u ubuntu sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi
    
    # Install zsh plugins
    sudo -u ubuntu git clone https://github.com/zsh-users/zsh-autosuggestions /home/ubuntu/.oh-my-zsh/custom/plugins/zsh-autosuggestions || true
    sudo -u ubuntu git clone https://github.com/zsh-users/zsh-syntax-highlighting /home/ubuntu/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting || true
    sudo -u ubuntu git clone https://github.com/zsh-users/zsh-completions /home/ubuntu/.oh-my-zsh/custom/plugins/zsh-completions || true
    
    # Configure zsh
    sudo -u ubuntu sed -i 's/plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions docker npm node python vscode)/' /home/ubuntu/.zshrc
    
    # Create custom aliases
    cat >> /home/ubuntu/.zshrc << 'EOF'

# Custom aliases
alias ll='ls -laF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gd='git diff'
alias gb='git branch'
alias gco='git checkout'
alias docker-compose='docker compose'
alias dc='docker compose'
alias dcu='docker compose up -d'
alias dcd='docker compose down'
alias dcl='docker compose logs'
alias dps='docker ps'
alias di='docker images'
alias dcex='docker compose exec'

# Development shortcuts
alias serve='python3 -m http.server'
alias activate='source venv/bin/activate'
alias pip-upgrade='pip install --upgrade pip'
alias node-upgrade='n latest'

# System info
alias sysinfo='neofetch'
alias weather='curl wttr.in'
alias speedtest='speedtest-cli'

EOF
    
    # Set zsh as default shell
    chsh -s /bin/zsh ubuntu
    
    log "Shell environment setup completed ✓"
}

# Setup development directories
setup_directories() {
    log "Setting up development directories..."
    
    # Create project structure
    sudo -u ubuntu mkdir -p /home/ubuntu/{projects,scripts,tools,temp,downloads}
    sudo -u ubuntu mkdir -p /home/ubuntu/projects/{web,api,scripts,tools,learning}
    
    # Create useful scripts
    cat > /home/ubuntu/scripts/new-project.sh << 'EOF'
#!/bin/bash
# Create a new project with basic structure

if [ $# -eq 0 ]; then
    echo "Usage: new-project <project-name> [type]"
    echo "Types: web, api, script, tool"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_TYPE=${2:-web}
PROJECT_DIR="/home/ubuntu/projects/$PROJECT_TYPE/$PROJECT_NAME"

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create basic structure based on type
case $PROJECT_TYPE in
    "web")
        mkdir -p {src,public,tests,docs}
        echo "# $PROJECT_NAME" > README.md
        echo "node_modules/" > .gitignore
        ;;
    "api")
        mkdir -p {src,tests,docs,config}
        echo "# $PROJECT_NAME API" > README.md
        echo "node_modules/" > .gitignore
        ;;
    "script")
        mkdir -p {src,tests}
        echo "# $PROJECT_NAME Script" > README.md
        echo "__pycache__/" > .gitignore
        ;;
    "tool")
        mkdir -p {bin,lib,tests}
        echo "# $PROJECT_NAME Tool" > README.md
        ;;
esac

git init
echo "Project $PROJECT_NAME created at $PROJECT_DIR"
EOF
    
    chmod +x /home/ubuntu/scripts/new-project.sh
    sudo -u ubuntu ln -sf /home/ubuntu/scripts/new-project.sh /home/ubuntu/.local/bin/new-project
    
    log "Development directories setup completed ✓"
}

# Setup VS Code Server
setup_vscode_server() {
    log "Setting up VS Code Server..."
    
    # Download and install VS Code Server
    cd /tmp
    VSCODE_VERSION=$(curl -s https://update.code.visualstudio.com/api/update/linux-x64/stable/latest | jq -r '.version')
    curl -L "https://update.code.visualstudio.com/commit/$(curl -s https://update.code.visualstudio.com/api/update/linux-x64/stable/latest | jq -r '.commit')/server-linux-x64/web/bin/code-${VSCODE_VERSION}.tar.gz" | tar xz
    
    mkdir -p /home/ubuntu/.vscode-server
    mv vscode-server-linux-x64 /home/ubuntu/.vscode-server/bin/
    chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server
    
    log "VS Code Server setup completed ✓"
}

# Setup monitoring and logging
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create system monitoring script
    cat > /home/ubuntu/scripts/system-status.sh << 'EOF'
#!/bin/bash
# System status monitoring script

echo "🖥️  System Status"
echo "================="
echo "Uptime: $(uptime -p)"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""
echo "💾 Memory Usage"
echo "==============="
free -h
echo ""
echo "💿 Disk Usage"
echo "============"
df -h | grep -E '^/dev/'
echo ""
echo "🌐 Network"
echo "=========="
ip addr show | grep -E 'inet.*scope global' || echo 'No global IP found'
echo ""
echo "🔥 Top Processes"
echo "==============="
ps aux --sort=-%cpu | head -6
echo ""
echo "🐳 Docker Status"
echo "================"
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Docker not installed"
fi
EOF
    
    chmod +x /home/ubuntu/scripts/system-status.sh
    sudo -u ubuntu ln -sf /home/ubuntu/scripts/system-status.sh /home/ubuntu/.local/bin/system-status
    
    log "Monitoring setup completed ✓"
}

# Create welcome message
create_welcome() {
    log "Creating welcome message..."
    
    cat > /etc/motd << 'EOF'
🚀 Oracle Cloud Development Server
===================================

✅ Development Environment Ready!
   • Ubuntu 22.04 LTS
   • Docker & Docker Compose
   • Node.js 18.x + npm/yarn/pnpm
   • Python 3 + pip/poetry
   • Git + useful tools
   • Oh My Zsh with plugins
   • VS Code Server

🔧 Quick Commands:
   • system-status    - Show system status
   • new-project      - Create new project
   • docker-compose   - Docker Compose management
   • code             - Open VS Code Server

📁 Project Directories:
   • ~/projects/web   - Web projects
   • ~/projects/api   - API projects
   • ~/projects/scripts - Scripts
   • ~/projects/tools - Tools

🌟 Happy Coding! 🎉
EOF
    
    log "Welcome message created ✓"
}

# Final cleanup and optimization
finalize_setup() {
    log "Finalizing setup..."
    
    # Clean up package cache
    apt-get clean
    
    # Optimize shell startup
    sudo -u ubuntu touch /home/ubuntu/.zshrc
    
    # Set proper permissions
    chown -R ubuntu:ubuntu /home/ubuntu
    
    # Create a startup script that runs on login
    cat > /home/ubuntu/.zprofile << 'EOF'
# Display system status on login
if command -v neofetch &> /dev/null; then
    neofetch
else
    echo "🚀 Oracle Cloud Development Server Ready!"
fi
EOF
    
    log "Setup finalized ✓"
}

# Main execution
main() {
    echo "🔧 Remote Server Setup Starting..."
    echo "=================================="
    
    update_system
    install_dev_tools
    setup_python
    setup_nodejs
    setup_docker
    setup_git
    setup_shell
    setup_directories
    setup_vscode_server
    setup_monitoring
    create_welcome
    finalize_setup
    
    echo ""
    log "🎉 Remote server setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Reconnect to the server: ssh oracle-dev-server"
    echo "   2. Start coding: new-project my-app web"
    echo "   3. Check system: system-status"
    echo ""
}

# Run main function
main "$@"
