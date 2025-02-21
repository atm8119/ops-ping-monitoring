#!/usr/bin/env python3
"""
Enable VM Ping Monitoring for VCF Operations

This script provides functionality to enable ping monitoring for Virtual Machines
in VCF Operations. It supports enabling monitoring for single VMs, multiple VMs,
or all VMs in the environment.

Features:
    - Interactive and command-line modes
    - State tracking to avoid reprocessing
    - Detailed logging
    - Token refresh handling
    - Error recovery

Usage:
    Interactive mode:
        python Enable_VM_Ping_Monitoring.py

    Command-line mode:
        python Enable_VM_Ping_Monitoring.py --vm-name vm1 vm2 --force
        python Enable_VM_Ping_Monitoring.py --all-vms
"""

import json
import os
import logging
import argparse
from typing import Dict, List, Optional
import requests
import time
import warnings
from datetime import datetime
import urllib3
import Fetch_New_Bearer_Token_VCF_Ops

# Warnings configuration --- Suppress specifically InsecureRequestWarning during execution
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Notice (if InsecureRequestWarnings occur)
def print_security_notice():
    """Print a clear security notice about SSL verification"""
    print("\n" + "=" * 80)
    print("Security Notice:")
    print("-" * 80)
    print("This script is currently running with SSL verification disabled for VCF Operations.")
    print("This setting is typically used in test environments with self-signed certificates.")
    print("\nAction Items for Production Use:")
    print("1. Configure proper SSL certificates in your VCF Operations environment")
    print("2. Update the script to enable SSL verification")
    print("3. Or add your CA certificate to the trusted store")
    print("\nFor more information, visit:")
    print("https://techdocs.broadcom.com/us/en/vmware-cis/aria/aria-operations/8-18/vmware-aria-operations-configuration-guide-8-18/about-the-admin-ui/custom-vrealize-operations-manager-certificates/custom-certificate-requirements.html")
    print("=" * 80 + "\n")

## Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vm_ping_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

## Class for ping enablement methods
class PingEnablementManager:
    """Manages VM ping monitoring enablement in VCF Operations"""

    def __init__(self, ops_fqdn: str, state_file: str = "ping_enabled_vms.json"):
        """
        Initialize the PingEnablementManager.

        Args:
            ops_fqdn: FQDN of the VCF Operations instance
            state_file: Path to the state tracking file
        """
        self.ops_fqdn = ops_fqdn
        self.state_file = state_file
        self.processed_vms: Dict[str, datetime] = self._load_state()
        self.bearer_token = self._get_bearer_token()
        self.made_insecure_request = False
        logger.info(f"Initialized PingEnablementManager for {ops_fqdn}")

    def _make_request(self, *args, **kwargs):
        """Wrapper for requests to track insecure connections"""
        if kwargs.get('verify') is False:
            self.made_insecure_request = True
        return requests.request(*args, **kwargs)

    def _get_bearer_token(self) -> str:
        """Get bearer token from file, refresh if needed"""
        token_file = "vcf-monitoring-accessToken.txt"
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
                logger.debug("Bearer token loaded from file")
                return token
        except FileNotFoundError:
            logger.info("Bearer token not found. Fetching new token...")
            Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()
            with open(token_file, 'r') as f:
                token = f.read().strip()
                logger.info("New bearer token generated and loaded")
                return token

    def _load_state(self) -> Dict[str, dict]:
        """Load the state of previously processed VMs"""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

                # Convert to new format if needed
                state = {}
                for vm_id, value in data.items():
                    if isinstance(value, str):
                        # Convert old timestamp format to new format
                        state[vm_id] = {
                            "name": "Unknown",
                            "first_processed": value,
                            "last_processed": value,
                            "ops_source": self.ops_fqdn
                        }
                    elif isinstance(value, dict):
                        # Remove ping_enabled flag and ensure ops_source
                        new_value = {
                            "name": value.get("name", "Unknown"),
                            "first_processed": value.get("first_processed", datetime.now().isoformat()),
                            "last_processed": value.get("last_processed", datetime.now().isoformat()),
                            "ops_source": value.get("ops_source", self.ops_fqdn)
                        }

                        # Add action if not present
                        if "action" not in new_value and "ping_enabled" in value:
                            new_value["action"] = "ping_enabled" if value["ping_enabled"] else "unknown"

                        state[vm_id] = new_value

                logger.debug(f"Loaded state file with {len(state)} entries")
                return state
        except FileNotFoundError:
            logger.debug("No existing state file found, starting fresh")
            return {}
        except json.JSONDecodeError:
            logger.warning("Corrupted state file found, starting fresh")
            return {}

    def _save_state(self):
        """Save the current state of processed VMs"""
        try:
            with open(self.state_file, 'w') as f:
                # Already storing structured data, so just dump directly
                json.dump(self.processed_vms, f, indent=2)
                logger.debug(f"Saved state with {len(self.processed_vms)} entries")
        except Exception as e:
            logger.error(f"Error saving state file: {str(e)}")

    def _vm_in_cache(self, vm_id: str) -> bool:
        """Check if VM is in cache with valid data"""
        return (vm_id in self.processed_vms and 
                isinstance(self.processed_vms[vm_id], dict))

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"OpsToken {self.bearer_token}"
        }

    def get_all_vms(self) -> List[Dict]:
        """Fetch all VMs from VCF Operations"""
        url = f"https://{self.ops_fqdn}/suite-api/api/resources"
        params = {
            "resourceKind": "VirtualMachine",
            "adapterKind": "VMWARE"
        }

        try:
            logger.debug(f"Fetching all VMs from {url}")
            response = self._make_request(
                method="GET",
                url=url,
                headers=self._get_headers(),
                params=params,
                verify=False
            )
            response.raise_for_status()
            vms = response.json().get('resourceList', [])
            logger.info(f"Successfully fetched {len(vms)} VMs")
            return vms
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning("Token expired, refreshing...")
                Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()
                self.bearer_token = self._get_bearer_token()
                return self.get_all_vms()
            logger.error(f"HTTP error while fetching VMs: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching VMs: {str(e)}")
            raise

    def get_specific_vms(self, vm_names: List[str]) -> List[Dict]:
        """Fetch specific VMs from VCF Operations"""
        url = f"https://{self.ops_fqdn}/suite-api/api/resources"
        all_vms = []
        retried = False

        for vm_name in vm_names:
            params = {
                "resourceKind": "VirtualMachine",
                "adapterKind": "VMWARE",
                "name": vm_name
            }

            try:
                logger.debug(f"Fetching VM: {vm_name}")
                response = self._make_request(
                    method="GET",
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    verify=False
                )
                response.raise_for_status()
                vms = response.json().get('resourceList', [])
                if vms:
                    logger.info(f"Found VM: {vm_name}")
                    all_vms.extend(vms)
                else:
                    logger.warning(f"VM not found: {vm_name}")
            except requests.exceptions.HTTPError as e:
                # If Error response due to expired token, retry once after fetching new Token
                if e.response.status_code == 401 and not retried:
                    logger.warning("Token expired, refreshing...")
                    Fetch_New_Bearer_Token_VCF_Ops.Fetch_New_Bearer_Token()
                    self.bearer_token = self._get_bearer_token()
                    retried = True
                    # Retry this VM
                    try:
                        response = self._make_request(
                            method="GET",
                            url=url,
                            headers=self._get_headers(),
                            params=params,
                            verify=False
                        )
                        response.raise_for_status()
                        vms = response.json().get('resourceList', [])
                        if vms:
                            logger.info(f"Found VM: {vm_name}")
                            all_vms.extend(vms)
                        else:
                            logger.warning(f"VM not found: {vm_name}")
                    except Exception as retry_e:
                        logger.error(f"Error fetching VM {vm_name} after token refresh: {str(retry_e)}")
                else:
                    logger.error(f"Error fetching VM {vm_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching VM {vm_name}: {str(e)}")

        return all_vms

    def update_ping_enabled(self, vm_data: Dict, force_update: bool = False) -> bool:
        """Update isPingEnabled for a VM if needed"""
        vm_id = vm_data['identifier']
        vm_name = vm_data['resourceKey']['name']

        # Check if in cache and should skip processing
        if not force_update and self._vm_in_cache(vm_id):
            logger.info(f"Skipping {vm_name} - already processed (cached)")
            return False

        # Check if update is needed
        needs_update = False
        for identifier in vm_data['resourceKey']['resourceIdentifiers']:
            if (identifier['identifierType']['name'] == 'isPingEnabled' and
                identifier['value'] != 'true'):
                needs_update = True
                break

        if needs_update:
            logger.info(f"Updating ping monitoring for {vm_name}")

            # Get required identifiers
            required_identifiers = []
            for identifier in vm_data['resourceKey']['resourceIdentifiers']:
                if identifier['identifierType']['name'] in ['isPingEnabled', 'VMEntityName',
                                                        'VMEntityObjectID', 'VMEntityVCID']:
                    if identifier['identifierType']['name'] == 'isPingEnabled':
                        identifier['value'] = 'true'
                    required_identifiers.append(identifier)

            # Construct minimal update payload
            update_payload = {
                "resourceKey": {
                    "name": vm_name,
                    "adapterKindKey": "VMWARE",
                    "resourceKindKey": "VirtualMachine",
                    "resourceIdentifiers": required_identifiers
                },
                "identifier": vm_id
            }

            # Make update request
            url = f"https://{self.ops_fqdn}/suite-api/api/resources"
            params = {"_no_links": "true"}

            try:
                logger.debug(f"Sending update request for {vm_name}")
                response = self._make_request(
                    method="PUT",
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=update_payload,
                    verify=False
                )
                response.raise_for_status()
                logger.info(f"Successfully updated {vm_name}")

                # Store enhanced metadata in cache
                current_time = datetime.now().isoformat()
                self.processed_vms[vm_id] = {
                    "name": vm_name,
                    "first_processed": self.processed_vms.get(vm_id, {}).get("first_processed", current_time),
                    "last_processed": current_time,
                    "ops_source": self.ops_fqdn,
                    "action": "ping_enabled"
                }
                return True
            except Exception as e:
                logger.error(f"Error updating {vm_name}: {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Response: {e.response.text}")
                return False
        else:
            logger.debug(f"No update needed for {vm_name} - isPingEnabled already true")
            # Update metadata in cache for skipped VMs
            current_time = datetime.now().isoformat()
            self.processed_vms[vm_id] = {
                "name": vm_name,
                "first_processed": self.processed_vms.get(vm_id, {}).get("first_processed", current_time),
                "last_processed": current_time,
                "ops_source": self.ops_fqdn,
                "action": "already_enabled"
            }
            return False

    def process_vms(self, vm_names: Optional[List[str]] = None, force_update: bool = False):
        """
        Process VMs and update isPingEnabled where needed.

        Args:
            vm_names: List of VM names to process, or None for all VMs
            force_update: Whether to force update even if previously processed
        """
        logger.info(f"Starting VM processing (force update: {force_update})")

        try:
            if vm_names is None:
                logger.info("Fetching all VMs...")
                vms = self.get_all_vms()
            else:
                logger.info(f"Fetching specified VMs: {', '.join(vm_names)}")
                vms = self.get_specific_vms(vm_names)

            logger.info(f"Found {len(vms)} VMs")
            if not vms:
                logger.warning("No VMs to process")
                return

            updates_made = 0
            start_time = time.time()

            for vm in vms:
                try:
                    if self.update_ping_enabled(vm, force_update):
                        updates_made += 1

                    # Save state periodically
                    if updates_made % 10 == 0:
                        self._save_state()
                except Exception as e:
                    logger.error(f"Error processing VM {vm.get('resourceKey', {}).get('name', 'Unknown')}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error during VM processing: {str(e)}")
            raise
        finally:
            # Always save state at the end
            self._save_state()

            end_time = time.time()
            logger.info(f"Processing complete:")
            logger.info(f"Total VMs processed: {len(vms)}")
            logger.info(f"Updates made: {updates_made}")
            logger.info(f"Time taken: {end_time - start_time:.2f} seconds")

## User-Experience Utility | CLI Parser
def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Enable ping monitoring for VMs in VCF Operations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Create mutually exclusive group for VM selection
    vm_group = parser.add_mutually_exclusive_group()
    vm_group.add_argument(
        '--vm-name',
        nargs='+',
        help='One or more VM names to process'
    )
    vm_group.add_argument(
        '--all-vms',
        action='store_true',
        help='Process all VMs in the environment'
    )

    # Other arguments
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if VM was previously processed'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    return parser.parse_args()

## Main Workflow
def main() -> Optional[PingEnablementManager]:
    """Main execution flow with support for both interactive and command-line modes"""
    args = parse_arguments()

    # Configure debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Load Operations Manager configuration
    try:
        with open('vcf-monitoring-loginData.json', 'r') as f:
            ops_config = json.load(f)
    except FileNotFoundError:
        logger.error("Configuration file 'vcf-monitoring-loginData.json' not found")
        print("\nPlease create vcf-monitoring-loginData.json from the template file.")
        return
    except json.JSONDecodeError:
        logger.error("Invalid JSON in configuration file")
        return

    manager = PingEnablementManager(ops_config['operationsHost'])

    try:

        # Command-line mode
        if args.vm_name or args.all_vms:
            vm_names = args.vm_name if args.vm_name else None
            manager.process_vms(vm_names=vm_names, force_update=args.force)
            return

        # Interactive mode
        print("\nVCF Operations VM Ping Enablement Manager")
        print("----------------------------------------")
        print("Select operation mode:")
        print("1. Process single VM")
        print("2. Process multiple VMs")
        print("3. Process ALL VMs")

        while True:
            choice = input("\nEnter choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("Invalid choice. Please enter 1, 2, or 3.")

        force_update = False
        vm_names = None

        if choice == '1':
            vm_name = input("\nEnter VM name: ").strip()
            if not vm_name:
                print("Operation cancelled: No VM name provided")
                return
            vm_names = [vm_name]

        elif choice == '2':
            print("\nEnter VM names (one per line, empty line to finish):")
            vm_names = []
            while True:
                vm_name = input().strip()
                if not vm_name:
                    break
                vm_names.append(vm_name)

            if not vm_names:
                print("Operation cancelled: No VM names provided")
                return

        # Ask about force update
        if choice != '3':  # For specific VMs, always ask about force update
            force_str = input("\nForce update even if previously processed? (y/N): ").strip().lower()
            force_update = force_str in ['y', 'yes']
        else:  # For ALL VMs, provide more options
            print("\nSelect processing mode:")
            print("1. Process only unprocessed VMs")
            print("2. Force process all VMs")
            while True:
                force_choice = input("Enter choice (1 or 2): ").strip()
                if force_choice in ['1', '2']:
                    force_update = force_choice == '2'
                    break
                print("Invalid choice. Please enter 1 or 2.")

        # Execute the processing
        manager.process_vms(vm_names=vm_names, force_update=force_update)

        # Show security notice if insecure requests were made
        if manager.made_insecure_request:
            print_security_notice()

        return manager

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return manager  # Return manager even on error to check insecure requests

## Execution starting point
if __name__ == "__main__":
    manager = None
    try:
        manager = main()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user")
        if manager and manager.made_insecure_request:
            print_security_notice()
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\nError: {str(e)}")
        print("Check vm_ping_monitoring.log for details")
        if manager and manager.made_insecure_request:
            print_security_notice()