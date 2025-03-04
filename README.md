# VCF Operations VM Ping Monitoring

This tool enables automated management of VM ping monitoring in VMware Cloud Foundation (VCF) Operations. It allows you to easily enable ping monitoring for virtual machines in your environment, both manually and via scheduled automation.

## Features

- **Multiple Operation Modes**:
  - Process a single VM
  - Process multiple VMs
  - Process all VMs in your environment
  - Schedule automated monitoring

- **Smart State Management**:
  - Tracks processed VMs to avoid unnecessary updates
  - Option to force update previously processed VMs
  - Maintains detailed metadata including:
    - First processing time
    - Last processing time
    - Source Operations instance

- **Scheduling Capabilities**:
  - Interval-based scheduling (minutes, hours, days)
  - Cron-based scheduling for complex time patterns
  - Daemon mode for background operation
  - Service integration for enterprise environments

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

3. (Optional) Create the scheduler configuration:
   ```bash
   cp vcf-monitoring-schedule.json.template vcf-monitoring-schedule.json
   ```

## Usage

### Interactive Mode

Run the script without arguments for interactive mode:
```bash
python Enable_VM_Ping_Monitoring.py
```

Follow the prompts to:
1. Choose operation mode (single VM, multiple VMs, ALL VMs, or scheduler management)
2. Enter VM names
3. Choose whether to force update previously processed VMs
4. Set up and manage scheduled monitoring

### Command-Line Mode

#### Direct Monitoring

Process specific VMs:
```bash
python Enable_VM_Ping_Monitoring.py run --vm-name vm1 vm2 vm3
```

Process all VMs:
```bash
python Enable_VM_Ping_Monitoring.py run --all-vms
```

#### Scheduler Management

Start the scheduler:
```bash
python Enable_VM_Ping_Monitoring.py schedule start
```

Start the scheduler as a daemon:
```bash
python Enable_VM_Ping_Monitoring.py schedule start --daemon
```

Check scheduler status:
```bash
python Enable_VM_Ping_Monitoring.py schedule status
```

Stop the scheduler:
```bash
python Enable_VM_Ping_Monitoring.py schedule stop
```

Run the scheduled job immediately:
```bash
python Enable_VM_Ping_Monitoring.py schedule run-now
```

Configure the scheduler:
```bash
# Set up daily interval
python Enable_VM_Ping_Monitoring.py schedule configure \
  --schedule-type interval \
  --interval-unit days \
  --interval-value 1 \
  --target-all-vms \
  --ignore-cache

# Set up weekly cron job
python Enable_VM_Ping_Monitoring.py schedule configure \
  --schedule-type cron \
  --cron-expression "0 0 * * 0" \
  --target-vms vm1 vm2 vm3 \
  --use-cache
```

### Common Options

- `--force`: Update VMs even if previously processed
- `--debug`: Enable detailed debug logging
- `--vm-name`: Specify one or more VM names
- `--all-vms`: Process all VMs in the environment

## Scheduling Configuration

The scheduler supports two types of schedules:

### Interval-based Scheduling

Run at regular intervals:
- Minutes (e.g., every 30 minutes)
- Hours (e.g., every 12 hours)
- Days (e.g., every 1 day)

### Cron-based Scheduling

Run at specific times using cron expressions:
- Daily at midnight: `0 0 * * *`
- Daily at noon: `0 12 * * *`
- Weekly on Sunday: `0 0 * * 0`
- Monthly on the 1st: `0 0 1 * *`
- Custom expressions

## Running as a System Service

For enterprise environments, you can configure the scheduler to run as a system service.

### Linux (systemd)

1. Copy the service file:
   ```bash
   sudo cp vcf-ops-monitoring.service /etc/systemd/system/
   ```

2. Edit the service file to match your installation paths

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vcf-ops-monitoring.service
   sudo systemctl start vcf-ops-monitoring.service
   ```

4. Check service status:
   ```bash
   sudo systemctl status vcf-ops-monitoring.service
   ```

### Windows

1. Install NSSM (Non-Sucking Service Manager):
   ```
   choco install nssm
   ```

2. Create a service:
   ```
   nssm install VCFOpsMonitoring
   ```

3. Configure the service with the path to your Python executable and script

## Logging

The tool maintains detailed logs:

- **VM Monitoring**: `vm_ping_monitoring.log`
- **Scheduler**: `vm_ping_scheduler.log`

These logs include:
- Operation progress
- API responses
- Error details
- State changes
- Scheduling events

## State Management

The script maintains state in:

- **VM Processing State**: `ping_enabled_vms.json`
- **Scheduler Configuration**: `vcf-monitoring-schedule.json`

This state tracking enables:
- Skipping already processed VMs
- Historical tracking of operations
- Cross-environment awareness
- Reliable scheduling

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

4. **Scheduler Not Starting**
   - Check permissions
   - Verify Python path
   - Check logs for errors

### Debug Mode

For detailed troubleshooting, use debug mode:
```bash
python Enable_VM_Ping_Monitoring.py run --debug
python Enable_VM_Ping_Monitoring.py schedule status --debug
```

## Security Considerations

- The script defaults to SSL verification disabled for lab environments
- For production use:
  - Configure proper SSL certificates
  - Enable SSL verification
  - Or add your CA certificate to the trusted store
- Store credentials securely
- Run the scheduler with minimal permissions

## Examples

### Direct Monitoring Examples

1. Process a single VM:
   ```bash
   python Enable_VM_Ping_Monitoring.py run --vm-name vcf-m01-opscp02
   ```

2. Process multiple VMs with force update:
   ```bash
   python Enable_VM_Ping_Monitoring.py run --vm-name vm1 vm2 vm3 --force
   ```

3. Process all VMs in debug mode:
   ```bash
   python Enable_VM_Ping_Monitoring.py run --all-vms --debug
   ```

### Scheduling Examples

1. Configure a daily schedule for all VMs:
   ```bash
   python Enable_VM_Ping_Monitoring.py schedule configure \
     --schedule-type interval \
     --interval-unit days \
     --interval-value 1 \
     --target-all-vms
   ```

2. Start the scheduler as a daemon:
   ```bash
   python Enable_VM_Ping_Monitoring.py schedule start --daemon
   ```

3. Check scheduler status:
   ```bash
   python Enable_VM_Ping_Monitoring.py schedule status
   ```

4. Configure weekly maintenance window:
   ```bash
   python Enable_VM_Ping_Monitoring.py schedule configure \
     --schedule-type cron \
     --cron-expression "0 2 * * 0" \
     --target-all-vms \
     --ignore-cache
   ```

## Project Structure
```
ops-ping-monitoring/
├── Enable_VM_Ping_Monitoring.py     # Main script
├── scheduler.py                     # Scheduling module
├── Fetch_New_Bearer_Token_VCF_Ops.py # Token management
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── vcf-monitoring-loginData.json.template # Auth config template
├── vcf-monitoring-schedule.json.template # Schedule config template
├── vcf-ops-monitoring.service       # Systemd service file
└── .gitignore                       # Git ignore file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

By using, modifying, or distributing this code, you agree to the terms and conditions of the MIT License. This includes:

- The right to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software
- The requirement to include the original copyright notice and MIT License in any substantial portions of the code
- The understanding that the software is provided "as is", without warranty of any kind

For the full license text and terms, please see the [LICENSE](LICENSE) file in this repository.

## Contributing

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project. If you do not agree with these terms, please do not contribute to the project.

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting guide above
2. Review the logs
3. Submit an issue on GitHub