# VCF Operations VM Ping Monitoring

This tool enables automated management of VM ping monitoring in VMware Cloud Foundation (VCF) Operations. It allows you to easily enable ping monitoring for virtual machines in your environment.

## Features

- **Multiple Operation Modes**:
  - Process a single VM
  - Process multiple VMs
  - Process all VMs in your VCF Operations inventory

- **Smart State Management**:
  - Tracks processed VMs to avoid unnecessary updates
  - Option to force update previously processed VMs

- **Robust Error Handling**:
  - Automatic token refresh
  - Detailed logging
  - Comprehensive error reporting

- **User-Friendly Interface**:
  - Interactive CLI mode
  - Command-line arguments for automation
  - Clear progress feedback

## Prerequisites

- Python 3.8 or higher
- Access to VCF Operations instance
- Administrator credentials for VCF Operations

## Installation

1. Clone this repository or download the files to your local machine:
   ```bash
   git clone <repository-url>
   cd ops-ping-monitoring
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate on Windows
   venv\Scripts\activate

   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create your configuration file by copying the template:
   ```bash
   cp vcf-monitoring-loginData.json.template vcf-monitoring-loginData.json
   ```

2. Edit `vcf-monitoring-loginData.json` with your VCF Operations details:
   ```json
   {
       "operationsHost": "vcf-ops.example.com",
       "loginData": {
           "username": "admin@example.com",
           "authSource": "vIDMAuthSource",
           "password": "your-password"
       }
   }
   ```

## Usage

### Interactive Mode

Run the script without arguments for interactive mode:
```bash
python Enable_VM_Ping_Monitoring.py
```

Follow the prompts to:
1. Choose operation mode (single VM, multiple VMs, or ALL VMs)
2. Enter VM names
3. Choose whether to force update previously processed VMs

### Command-Line Mode

Process specific VMs:
```bash
python Enable_VM_Ping_Monitoring.py --vm-name vm1 vm2 vm3
```

Process all VMs:
```bash
python Enable_VM_Ping_Monitoring.py --all-vms
```

Additional options:
```bash
python Enable_VM_Ping_Monitoring.py --help
```

## Common Options

- `--force`: Update VMs even if previously processed
- `--debug`: Enable detailed debug logging
- `--vm-name`: Specify one or more VM names
- `--all-vms`: Process all VMs in the environment

## Logging

The script maintains detailed logs in `vm_ping_monitoring.log`, which includes:
- Operation progress
- API responses
- Error details
- State changes

## State Management

The script maintains state in `ping_enabled_vms.json` to track:
- Processed VMs
- Processing timestamps
- Update history

## Troubleshooting

### Common Issues

1. **Token Expired**
   - The script automatically handles token refresh
   - No action needed

2. **VM Not Found**
   - Verify VM name spelling
   - Check VM exists in VCF Operations inventory

3. **Connection Issues**
   - Verify network connectivity
   - Check VCF Operations FQDN
   - Verify credentials

### Debug Mode

For detailed troubleshooting, use debug mode:
```bash
python Enable_VM_Ping_Monitoring.py --debug
```

## Security Considerations

- The script defaults to SSL verification disabled for lab environments
- For production use:
  - Configure proper SSL certificates
  - Enable SSL verification
  - Or add your CA certificate to the trusted store

## Examples

1. Process a single VM:
   ```bash
   python Enable_VM_Ping_Monitoring.py --vm-name vcf-m01-opscp02
   ```

2. Process multiple VMs with force update:
   ```bash
   python Enable_VM_Ping_Monitoring.py --vm-name vm1 vm2 vm3 --force
   ```

3. Process all VMs in debug mode:
   ```bash
   python Enable_VM_Ping_Monitoring.py --all-vms --debug
   ```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions:
1. Check the troubleshooting guide above
2. Review the logs
3. Submit an issue on GitHub

## Project Structure
```
ops-ping-monitoring/
├── Enable_VM_Ping_Monitoring.py     # Main script
├── Fetch_New_Bearer_Token_VCF_Ops.py # Token management
├── requirements.txt                  # Python dependencies
├── README.md                        # This file
├── vcf-monitoring-loginData.json.template # Config template
└── .gitignore                       # Git ignore file
```
