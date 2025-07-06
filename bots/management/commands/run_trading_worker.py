from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Run the Celery trading worker for processing trade signals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='Number of worker processes (default: 4)'
        )
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error'],
            help='Log level (default: info)'
        )
        parser.add_argument(
            '--queues',
            type=str,
            default='trading',
            help='Comma-separated list of queues to process (default: trading)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Celery trading worker...')
        )
        
        # Build the celery worker command
        cmd = [
            'celery',
            '-A', 'traderelay_webapp',
            'worker',
            '--loglevel=' + options['loglevel'],
            '--concurrency=' + str(options['concurrency']),
            '--queues=' + options['queues'],
            '--hostname=trading-worker@%h',
            '--pidfile=/tmp/trading-worker.pid',
        ]
        
        try:
            # Run the celery worker
            self.stdout.write(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Celery worker failed with exit code {e.returncode}')
            )
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Trading worker stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running trading worker: {e}')
            )
            sys.exit(1) 