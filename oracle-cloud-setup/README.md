# Oracle Cloud Development Server Setup

🚀 **Complete automated deployment of an Oracle Cloud Free Tier development server with all tools pre-installed.**

## Features

- ✅ **One-click deployment** - Fully automated Terraform infrastructure setup
- ✅ **Zero manual configuration** - SSH config, keys, and connections handled automatically  
- ✅ **Complete dev stack** - Node.js, Python, Docker, Git, and more pre-installed
- ✅ **VS Code ready** - Remote SSH workspace configured out of the box
- ✅ **Reusable workflow** - Windsurf action for instant redeployment

## Prerequisites

1. **Oracle Cloud Account** with Free Tier enabled
2. **OCI CLI installed and configured**:
   ```bash
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   oci setup config
   ```
3. **API Key generated** in Oracle Cloud console
4. **Required tools**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install terraform jq
   
   # macOS  
   brew install terraform jq
   ```

## Quick Start

### 1. Clone and Deploy
```bash
cd oracle-cloud-setup
chmod +x deploy-oracle-server.sh
./deploy-oracle-server.sh
```

### 2. Click "Apply" when prompted
The script will pause for confirmation before deploying resources to your Oracle Cloud account.

### 3. Wait for completion
The entire process takes ~10-15 minutes:
- Terraform deployment: 5-8 minutes
- Server initialization: 3-5 minutes  
- Dev tools installation: 2-3 minutes

## What Gets Installed

### Infrastructure
- Ubuntu 22.04 LTS VM (Free Tier: VM.Standard.E2.1.Micro)
- 1 OCPU, 1GB RAM, 50GB boot volume
- Public IP with SSH access
- VCN, subnet, security groups, internet gateway

### Development Stack
- **Runtime**: Node.js 18.x, Python 3.11
- **Containers**: Docker, Docker Compose
- **Package Managers**: npm, yarn, pnpm, pip, poetry
- **Tools**: Git, VS Code Server, Oh My Zsh
- **Utilities**: jq, yq, httpie, ripgrep, fzf, bat, exa

### Development Environment
- Pre-configured shell aliases and functions
- Project scaffolding script (`new-project`)
- System monitoring (`system-status`)
- Organized directory structure
- SSH keys and configuration

## Connection Details

After deployment, connect with:

```bash
# SSH connection
ssh oracle-dev-server

# Open in VS Code
code --remote ssh-remote+oracle-dev-server /home/ubuntu

# Check system status
system-status
```

## Directory Structure

```
/home/ubuntu/
├── projects/          # Your development projects
│   ├── web/          # Web applications
│   ├── api/          # API projects
│   ├── scripts/      # Utility scripts
│   └── tools/        # Development tools
├── scripts/          # Utility scripts
├── tools/            # Development tools
└── downloads/        # Downloads directory
```

## Windsurf Action

The setup creates a reusable Windsurf action for one-click deployment:

**Location**: `.windsurf/actions/deploy-oracle-server.json`

**Usage**: Run the action from Windsurf to instantly deploy a new development server.

## Manual Operations

### Destroy Infrastructure
```bash
cd terraform
terraform destroy -auto-approve
```

### Update SSH Config
```bash
# Update with new IP
./deploy-oracle-server.sh --update-ssh-only
```

### Reinstall Dev Tools
```bash
ssh oracle-dev-server
sudo /tmp/remote-setup.sh
```

## Troubleshooting

### SSH Connection Issues
```bash
# Check SSH config
cat ~/.ssh/config

# Test connection manually
ssh -i ./oci-dev-key ubuntu@<PUBLIC_IP>

# Reset SSH known hosts
ssh-keygen -R <PUBLIC_IP>
```

### Terraform Issues
```bash
# Re-initialize Terraform
cd terraform
rm -rf .terraform*
terraform init

# Check OCI configuration
oci setup config
oci setup bootstrap
```

### Server Setup Issues
```bash
# Check cloud-init logs
ssh oracle-dev-server
sudo cat /var/log/cloud-init-output.log

# Re-run setup manually
ssh oracle-dev-server
sudo bash /tmp/remote-setup.sh
```

## Cost Management

### Free Tier Limits
- **Compute**: 4 AMD-based CPUs, 24 GB RAM
- **Storage**: 200 GB block volume, 100 GB object storage
- **Egress**: 10 TB/month data transfer
- **Load Balancer**: 1 load balancer

### Monitoring Usage
```bash
# Check Oracle Cloud usage
oci compute instance list --compartment-id <COMPARTMENT_ID>

# Monitor costs
oci usage-customer reward-usage list
```

### Cost Optimization
- Use the `VM.Standard.E2.1.Micro` shape (always free)
- Shut down when not in use:
  ```bash
  ssh oracle-dev-server
  sudo shutdown -h now
  ```

## Security

### SSH Security
- RSA 4096-bit keys generated automatically
- SSH config with strict host key checking disabled for automation
- Public key authentication only

### Network Security
- Security groups allow only necessary ports (22, 80, 443)
- Private subnet with internet gateway
- No unnecessary services exposed

### Best Practices
- Regular security updates enabled
- Non-root user for development
- Docker user group configured
- API keys with minimal permissions

## Customization

### Modify Terraform Configuration
Edit `terraform/main.tf` to change:
- VM shape and size
- Network configuration
- Security group rules
- Storage settings

### Customize Dev Tools
Edit `remote-setup.sh` to add:
- Additional programming languages
- Specific package versions
- Custom scripts and tools
- IDE configurations

### Environment Variables
Create `.env` file:
```bash
# Custom environment variables
NODE_VERSION=18
PYTHON_VERSION=3.11
DEFAULT_REGION=uk-london-1
```

## Support

### Documentation
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [OCI CLI Documentation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
- [Terraform Provider for Oracle Cloud](https://registry.terraform.io/providers/oracle/oci/latest/docs)

### Common Issues
1. **API Key Errors**: Ensure API key is properly configured in OCI CLI
2. **Compartment Issues**: Check compartment ID permissions
3. **SSH Timeouts**: Wait longer for VM initialization
4. **Resource Limits**: Verify Free Tier availability in your region

---

**🎉 Your Oracle Cloud development server is ready in minutes, not hours!**
