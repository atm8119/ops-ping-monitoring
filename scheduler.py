#!/usr/bin/env python3
"""
Scheduler for VCF Operations VM Ping Monitoring

This module provides scheduling capabilities for the VCF Operations VM Ping Monitoring tool.
It allows automatic execution of monitoring tasks at specified intervals or specific times.

Features:
    - Interval-based scheduling (minutes, hours, days)
    - Cron-based scheduling for complex time patterns
    - Schedule persistence across restarts
    - Status reporting
    - Daemon mode operation
"""

import os
import json
import logging
import time
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

# Local imports
import Enable_VM_Ping_Monitoring as monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vm_ping_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration file path
DEFAULT_CONFIG_PATH = 'vcf-monitoring-schedule.json'

# Default schedule configuration
DEFAULT_SCHEDULE_CONFIG = {
    "schedule_type": "interval",
    "interval_unit": "days",
    "interval_value": 1,
    "cron_expression": "0 0 * * *",  # Daily at midnight
    "vm_names": None,  # All VMs
    "force_update": False,
    "enabled": False,
    "last_run": None,
    "next_run": None
}

class MonitoringScheduler:
    """Scheduler for VCF Operations VM Ping Monitoring"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize the MonitoringScheduler.

        Args:
            config_path: Path to the scheduler configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.scheduler = BackgroundScheduler()
        self.job_id = 'vm_ping_monitoring'
        self.pid_file = 'vm_ping_scheduler.pid'
        self.stop_event = threading.Event()
        logger.info("Initialized MonitoringScheduler")

    def _load_config(self) -> Dict:
        """Load scheduler configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.debug(f"Loaded configuration from {self.config_path}")
                return config
            else:
                logger.info(f"Configuration file {self.config_path} not found, using defaults")
                return DEFAULT_SCHEDULE_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return DEFAULT_SCHEDULE_CONFIG.copy()

    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.debug(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")

    def _update_schedule_times(self):
        """Update the last and next run times in configuration"""
        try:
            if self.job_id in self.scheduler.get_jobs():
                job = self.scheduler.get_job(self.job_id)
                self.config['last_run'] = job.next_run_time.isoformat() if job.next_run_time else None
                self.config['next_run'] = job.next_run_time.isoformat() if job.next_run_time else None
                self._save_config()
        except Exception as e:
            logger.error(f"Error updating schedule times: {str(e)}")

    def _create_trigger(self):
        """Create a trigger based on configuration"""
        if self.config['schedule_type'] == 'interval':
            unit = self.config['interval_unit']
            value = self.config['interval_value']

            if unit == 'minutes':
                return IntervalTrigger(minutes=value)
            elif unit == 'hours':
                return IntervalTrigger(hours=value)
            elif unit == 'days':
                return IntervalTrigger(days=value)
            else:
                logger.warning(f"Unknown interval unit {unit}, defaulting to daily")
                return IntervalTrigger(days=1)
        elif self.config['schedule_type'] == 'cron':
            try:
                return CronTrigger.from_crontab(self.config['cron_expression'])
            except Exception as e:
                logger.error(f"Invalid cron expression: {str(e)}")
                return IntervalTrigger(days=1)
        else:
            logger.warning(f"Unknown schedule type {self.config['schedule_type']}, defaulting to daily interval")
            return IntervalTrigger(days=1)

    def _job_function(self):
        """Execute the monitoring job"""
        try:
            logger.info("Starting scheduled VM ping monitoring")

            # Load VCF Operations configuration
            try:
                with open('vcf-monitoring-loginData.json', 'r') as f:
                    ops_config = json.load(f)
            except FileNotFoundError:
                logger.error("Configuration file 'vcf-monitoring-loginData.json' not found")
                return
            except json.JSONDecodeError:
                logger.error("Invalid JSON in configuration file")
                return

            # Create manager and process VMs
            manager = monitor.PingEnablementManager(ops_config['operationsHost'])
            vm_names = self.config['vm_names']
            force_update = self.config['force_update']

            manager.process_vms(vm_names=vm_names, force_update=force_update)

            logger.info("Completed scheduled VM ping monitoring")

            # Update last run timestamp
            self.config['last_run'] = datetime.now().isoformat()
            self._save_config()

        except Exception as e:
            logger.error(f"Error in scheduled job: {str(e)}")

    def start(self, daemon_mode: bool = False):
        """
        Start the scheduler.

        Args:
            daemon_mode: Whether to run as a daemon process
        """
        if self.is_running():
            logger.warning("Scheduler is already running")
            print("\nThe scheduler is already running.")
            return False

        try:
            # Create the job
            trigger = self._create_trigger()
            self.scheduler.add_job(
                self._job_function,
                trigger=trigger,
                id=self.job_id,
                name='VM Ping Monitoring'
            )

            # Start the scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully")

            # Update configuration
            self.config['enabled'] = True
            self._update_schedule_times()
            self._save_config()

            # Create PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))

            # Get job info for nicer output
            job = self.scheduler.get_job(self.job_id)
            next_run_time = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Not scheduled"

            # Print nicer user information
            print("\n✅ VM Ping Monitoring Scheduler Started Successfully")
            print("\n📋 Current Configuration:")

            # Format schedule info
            schedule_desc = format_schedule_description(self.config)
            print(f"  • Schedule: {schedule_desc}")

            # Target VM info
            vm_names = self.config.get('vm_names', None)
            if vm_names:
                vm_str = ', '.join(vm_names)
                print(f"  • Target VMs: {vm_str}")
            else:
                print("  • Target VMs: ALL VMs in environment")

            # Cache behavior
            force_update = self.config.get('force_update', False)
            print(f"  • Cache mode: {'Ignore cache' if force_update else 'Use cache (only process new/changed VMs)'}")

            print(f"\n⏱️  Next scheduled run: {next_run_time}")

            print("\n📌 Available commands:")
            print("  • Check status:   python Enable_VM_Ping_Monitoring.py schedule status")
            print("  • Run now:        python Enable_VM_Ping_Monitoring.py schedule run-now")
            print("  • Reconfigure:    python Enable_VM_Ping_Monitoring.py schedule configure --help")
            print("  • Stop scheduler: python Enable_VM_Ping_Monitoring.py schedule stop")

            if daemon_mode:
                print("\nRunning in daemon mode (press Ctrl+C to stop)")
                # Wait until stop event is set or keyboard interrupt
                try:
                    while not self.stop_event.is_set():
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt detected")
                    print("\nStopping scheduler due to keyboard interrupt...")
                    self.stop()
                    print("Scheduler stopped.")
                finally:
                    if not self.stop_event.is_set():
                        self.stop()

            return True

        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            print(f"\n❌ Error starting scheduler: {str(e)}")
            return False

    def stop(self):
        """Stop the scheduler"""
        try:
            was_running = self.scheduler.running

            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")

            # Update configuration
            self.config['enabled'] = False
            self._save_config()

            # Remove PID file
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)

            # Set stop event
            self.stop_event.set()

            # Print user-friendly output
            if was_running:
                print("\n✅ VM Ping Monitoring Scheduler successfully stopped")
            else:
                print("\nℹ️ Scheduler was not running")

            print("\n📌 Available commands:")
            print("  • Start scheduler: python Enable_VM_Ping_Monitoring.py schedule start")
            print("  • Check status:    python Enable_VM_Ping_Monitoring.py schedule status")
            print("  • Run now:         python Enable_VM_Ping_Monitoring.py schedule run-now")

            return True
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            print(f"\n❌ Error stopping scheduler: {str(e)}")
            return False

    def is_running(self) -> bool:
        """Check if the scheduler is running"""
        # Check if PID file exists
        if os.path.exists(self.pid_file):
            try:
                # Read the PID and check if process is running
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())

                # Check if process exists
                try:
                    os.kill(pid, 0)  # Sends signal 0 to check process existence
                    return True
                except OSError:
                    # Process doesn't exist, clean up PID file
                    os.remove(self.pid_file)
                    return False
            except Exception:
                return False
        return False

    def status(self) -> Dict:
        """Get the scheduler status"""
        status = {
            "running": self.is_running(),
            "config": self.config,
            "job_info": None
        }

        if self.scheduler.running:
            try:
                job = self.scheduler.get_job(self.job_id)
                if job:
                    status["job_info"] = {
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                        "pending": job.pending
                    }
            except Exception as e:
                logger.error(f"Error getting job status: {str(e)}")

        return status

    def run_now(self):
        """Run the job immediately"""
        logger.info("Running VM ping monitoring job now")
        self._job_function()
        return True

    def configure(self, config: Dict):
        """
        Update scheduler configuration.

        Args:
            config: Dictionary with configuration values to update
        """
        # Update values
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value

        # Save configuration
        self._save_config()

        # Reconfigure job if scheduler is running
        if self.scheduler.running:
            try:
                # Remove existing job
                self.scheduler.remove_job(self.job_id)

                # Add new job with updated configuration
                trigger = self._create_trigger()
                self.scheduler.add_job(
                    self._job_function,
                    trigger=trigger,
                    id=self.job_id,
                    name='VM Ping Monitoring'
                )

                # Update schedule times
                self._update_schedule_times()

                logger.info("Scheduler reconfigured successfully")
            except Exception as e:
                logger.error(f"Error reconfiguring scheduler: {str(e)}")

# Helper Methods Called by Class
# ------------------------------
def process_friendly_schedule_options(args):
    """Process user-friendly scheduling options and convert to config updates."""
    config_updates = {}

    # Process --daily option
    if hasattr(args, 'daily') and args.daily is not None:
        try:
            time_parts = args.daily.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                print(f"\n❌ Invalid time format: {args.daily}. Please use HH:MM in 24-hour format (00-23:00-59)")
                return None

            # Convert to cron expression: minute hour * * *
            config_updates['schedule_type'] = 'cron'
            config_updates['cron_expression'] = f"{minute} {hour} * * *"
            return config_updates
        except ValueError:
            print(f"\n❌ Invalid time format: {args.daily}. Please use HH:MM in 24-hour format")
            return None

    # Process --weekly option
    if hasattr(args, 'weekly') and args.weekly is not None:
        if len(args.weekly) < 1:
            print("\n❌ Weekly schedule requires at least the day of week")
            return None

        # Parse day of week
        day_str = args.weekly[0].lower()
        day_mapping = {
            'mon': 1, 'monday': 1,
            'tue': 2, 'tuesday': 2,
            'wed': 3, 'wednesday': 3,
            'thu': 4, 'thursday': 4,
            'fri': 5, 'friday': 5,
            'sat': 6, 'saturday': 6,
            'sun': 0, 'sunday': 0
        }

        if day_str not in day_mapping:
            print(f"\n❌ Invalid day of week: {day_str}. Use mon, tue, wed, thu, fri, sat, or sun")
            return None

        day_of_week = day_mapping[day_str]

        # Parse time if provided
        hour = 0
        minute = 0

        if len(args.weekly) > 1:
            try:
                time_parts = args.weekly[1].split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    print(f"\n❌ Invalid time format: {args.weekly[1]}. Please use HH:MM in 24-hour format (00-23:00-59)")
                    return None
            except ValueError:
                print(f"\n❌ Invalid time format: {args.weekly[1]}. Please use HH:MM in 24-hour format")
                return None

        # Convert to cron expression: minute hour * * day_of_week
        config_updates['schedule_type'] = 'cron'
        config_updates['cron_expression'] = f"{minute} {hour} * * {day_of_week}"
        return config_updates

    # Process --monthly option
    if hasattr(args, 'monthly') and args.monthly is not None:
        if len(args.monthly) < 1:
            print("\n❌ Monthly schedule requires at least the day of month")
            return None

        # Parse day of month
        try:
            day_of_month = int(args.monthly[0])
            if day_of_month < 1 or day_of_month > 31:
                print(f"\n❌ Invalid day of month: {day_of_month}. Must be between 1 and 31")
                return None
        except ValueError:
            print(f"\n❌ Invalid day of month: {args.monthly[0]}. Must be a number between 1 and 31")
            return None

        # Parse time if provided
        hour = 0
        minute = 0

        if len(args.monthly) > 1:
            try:
                time_parts = args.monthly[1].split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    print(f"\n❌ Invalid time format: {args.monthly[1]}. Please use HH:MM in 24-hour format (00-23:00-59)")
                    return None
            except ValueError:
                print(f"\n❌ Invalid time format: {args.monthly[1]}. Please use HH:MM in 24-hour format")
                return None

        # Convert to cron expression: minute hour day_of_month * *
        config_updates['schedule_type'] = 'cron'
        config_updates['cron_expression'] = f"{minute} {hour} {day_of_month} * *"
        return config_updates

    # Process --every option
    if hasattr(args, 'every') and args.every is not None:
        if len(args.every) != 2:
            print("\n❌ '--every' requires VALUE and UNIT arguments")
            return None

        # Parse value
        try:
            value = int(args.every[0])
            if value < 1:
                print(f"\n❌ Invalid value for --every: {value}. Must be a positive integer")
                return None
        except ValueError:
            print(f"\n❌ Invalid value for --every: {args.every[0]}. Must be a positive integer")
            return None

        # Parse unit
        unit = args.every[1].lower()
        valid_units = ['minute', 'minutes', 'hour', 'hours', 'day', 'days']

        if unit not in valid_units:
            print(f"\n❌ Invalid unit for --every: {unit}. Must be minutes, hours, or days")
            return None

        # Normalize unit (remove trailing 's' if present)
        if unit.endswith('s'):
            unit = unit[:-1]
        unit = unit + 's'  # Add 's' to make it plural for config

        # Convert to interval configuration
        config_updates['schedule_type'] = 'interval'
        config_updates['interval_value'] = value
        config_updates['interval_unit'] = unit
        return config_updates

    return config_updates

def format_schedule_description(config: Dict) -> str:
    """
    Format a human-readable description of the schedule.

    Args:
        config: Scheduler configuration

    Returns:
        str: Human-readable schedule description
    """
    if config['schedule_type'] == 'interval':
        unit = config['interval_unit']
        value = config['interval_value']

        if value == 1:
            # Make singular for value of 1
            unit_display = unit[:-1] if unit.endswith('s') else unit
        else:
            unit_display = unit

        return f"Every {value} {unit_display}"

    elif config['schedule_type'] == 'cron':
        cron_expr = config['cron_expression']
        parts = cron_expr.split()

        if len(parts) != 5:
            return f"Custom schedule: {cron_expr}"

        minute, hour, day_month, month, day_week = parts

        # Daily at specific time
        if day_month == '*' and month == '*' and day_week == '*':
            if hour == '0' and minute == '0':
                return "Daily at midnight"
            elif hour == '12' and minute == '0':
                return "Daily at noon"
            else:
                try:
                    hour_int = int(hour)
                    am_pm = 'am' if hour_int < 12 else 'pm'
                    hour_12 = hour_int if hour_int <= 12 else hour_int - 12
                    hour_12 = 12 if hour_12 == 0 else hour_12

                    if minute == '0':
                        return f"Daily at {hour_12}{am_pm}"
                    else:
                        return f"Daily at {hour_12}:{minute.zfill(2)}{am_pm}"
                except:
                    return f"Daily at {hour}:{minute}"

        # Weekly on specific day
        if day_month == '*' and month == '*' and day_week != '*':
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            try:
                day_index = int(day_week) % 7  # Convert to 0-6 range
                day_name = day_names[day_index]

                if hour == '0' and minute == '0':
                    return f"Weekly on {day_name} at midnight"
                elif hour == '12' and minute == '0':
                    return f"Weekly on {day_name} at noon"
                else:
                    hour_int = int(hour)
                    am_pm = 'am' if hour_int < 12 else 'pm'
                    hour_12 = hour_int if hour_int <= 12 else hour_int - 12
                    hour_12 = 12 if hour_12 == 0 else hour_12

                    if minute == '0':
                        return f"Weekly on {day_name} at {hour_12}{am_pm}"
                    else:
                        return f"Weekly on {day_name} at {hour_12}:{minute.zfill(2)}{am_pm}"
            except:
                pass

        # Monthly on specific day
        if day_month != '*' and month == '*' and day_week == '*':
            try:
                dom = int(day_month)

                # Handle day suffix
                if 4 <= dom <= 20 or 24 <= dom <= 30:
                    suffix = 'th'
                else:
                    suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(dom % 10, 'th')

                if hour == '0' and minute == '0':
                    return f"Monthly on the {dom}{suffix} at midnight"
                elif hour == '12' and minute == '0':
                    return f"Monthly on the {dom}{suffix} at noon"
                else:
                    hour_int = int(hour)
                    am_pm = 'am' if hour_int < 12 else 'pm'
                    hour_12 = hour_int if hour_int <= 12 else hour_int - 12
                    hour_12 = 12 if hour_12 == 0 else hour_12

                    if minute == '0':
                        return f"Monthly on the {dom}{suffix} at {hour_12}{am_pm}"
                    else:
                        return f"Monthly on the {dom}{suffix} at {hour_12}:{minute.zfill(2)}{am_pm}"
            except:
                pass

        # Fallback to simple descriptions for common patterns
        if cron_expr == "0 0 * * *":
            return "Daily at midnight"
        elif cron_expr == "0 12 * * *":
            return "Daily at noon"
        elif cron_expr == "0 0 * * 0":
            return "Weekly on Sunday at midnight"
        elif cron_expr == "0 0 1 * *":
            return "Monthly on the 1st at midnight"
        elif cron_expr == "0 0 1 1 *":
            return "Yearly on January 1st at midnight"
        else:
            return f"Custom schedule: {cron_expr}"

    return "Unknown schedule"


def format_status_output(status: Dict) -> str:
    """
    Format a human-readable status output.

    Args:
        status: Status dictionary from MonitoringScheduler.status()

    Returns:
        str: Formatted status string
    """
    output = []

    # Running status
    running = status['running']
    status_emoji = "🟢" if running else "🔴"
    output.append(f"{status_emoji} Status: {'RUNNING' if running else 'STOPPED'}")

    # Schedule information
    config = status['config']
    schedule_desc = format_schedule_description(config)
    output.append(f"⏰ Schedule: {schedule_desc}")

    # Target information
    vm_names = config.get('vm_names')
    if vm_names:
        vm_str = ', '.join(vm_names)
        output.append(f"🎯 Target VMs: {vm_str}")
    else:
        output.append("🎯 Target VMs: ALL VMs in environment")

    # Cache behavior
    force_update = config.get('force_update', False)
    output.append(f"💾 Cache behavior: {'Ignore cache (process all VMs)' if force_update else 'Use cache (only process new/changed VMs)'}")

    # Timing information
    last_run = config.get('last_run')
    if last_run:
        # Try to convert ISO format to more readable format
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(last_run)
            last_run_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            last_run_formatted = last_run
        output.append(f"⏮️ Last run: {last_run_formatted}")
    else:
        output.append("⏮️ Last run: Never")

    job_info = status.get('job_info')
    if job_info and job_info.get('next_run'):
        # Try to convert ISO format to more readable format
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(job_info['next_run'])
            next_run_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            next_run_formatted = job_info['next_run']
        output.append(f"⏭️ Next run: {next_run_formatted}")
    else:
        if running:
            output.append("⏭️ Next run: Not scheduled")
        else:
            output.append("⏭️ Next run: N/A (scheduler stopped)")

    # Add available commands
    output.append("\n📌 Available commands:")
    output.append("  • Check status:   python Enable_VM_Ping_Monitoring.py schedule status")
    output.append("  • Run now:        python Enable_VM_Ping_Monitoring.py schedule run-now")
    output.append("  • Reconfigure:    python Enable_VM_Ping_Monitoring.py schedule configure --help")

    if running:
        output.append("  • Stop scheduler: python Enable_VM_Ping_Monitoring.py schedule stop")
    else:
        output.append("  • Start scheduler: python Enable_VM_Ping_Monitoring.py schedule start")

    return "\n".join(output)


def create_daemon():
    """
    Create a daemon process by forking and detaching.

    Returns:
        bool: True if running in child process, False if in parent
    """
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Exit parent process
            return False
    except OSError as e:
        logger.error(f"Fork #1 failed: {e}")
        return False

    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Exit from second parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork #2 failed: {e}")
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    return True