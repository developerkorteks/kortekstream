from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from streamapp.models import APIEndpoint
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage API endpoints for dynamic anime scraping'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['list', 'add', 'update', 'delete', 'test', 'set-priority'],
            help='Action to perform'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='API endpoint name'
        )
        parser.add_argument(
            '--url',
            type=str,
            help='API endpoint URL'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Source domain for the API'
        )
        parser.add_argument(
            '--priority',
            type=int,
            default=0,
            help='Priority (higher number = higher priority)'
        )
        parser.add_argument(
            '--id',
            type=int,
            help='API endpoint ID for update/delete operations'
        )
        parser.add_argument(
            '--active',
            action='store_true',
            help='Set endpoint as active'
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Set endpoint as inactive'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_endpoints()
        elif action == 'add':
            self.add_endpoint(options)
        elif action == 'update':
            self.update_endpoint(options)
        elif action == 'delete':
            self.delete_endpoint(options)
        elif action == 'test':
            self.test_endpoint(options)
        elif action == 'set-priority':
            self.set_priority(options)

    def list_endpoints(self):
        """List all API endpoints"""
        endpoints = APIEndpoint.objects.all().order_by('-priority', 'name')
        
        if not endpoints:
            self.stdout.write(self.style.WARNING('No API endpoints found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {endpoints.count()} API endpoints:'))
        self.stdout.write('')
        
        for endpoint in endpoints:
            status = '✓ ACTIVE' if endpoint.is_active else '✗ INACTIVE'
            self.stdout.write(
                f'ID: {endpoint.id} | {endpoint.name} | Priority: {endpoint.priority} | {status}'
            )
            self.stdout.write(f'  URL: {endpoint.url}')
            self.stdout.write(f'  Domain: {endpoint.source_domain}')
            self.stdout.write(f'  Success Count: {endpoint.success_count}')
            self.stdout.write('')

    def add_endpoint(self, options):
        """Add a new API endpoint"""
        name = options.get('name')
        url = options.get('url')
        domain = options.get('domain')
        priority = options.get('priority')
        is_active = options.get('active', True)
        
        if not all([name, url]):
            raise CommandError('--name and --url are required for adding endpoints')
        
        try:
            with transaction.atomic():
                endpoint = APIEndpoint.objects.create(
                    name=name,
                    url=url,
                    source_domain=domain or '',
                    priority=priority,
                    is_active=is_active
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully added API endpoint: {endpoint.name}')
                )
                
                # Test the endpoint
                self.test_endpoint({'id': endpoint.id})
                
        except Exception as e:
            raise CommandError(f'Failed to add endpoint: {e}')

    def update_endpoint(self, options):
        """Update an existing API endpoint"""
        endpoint_id = options.get('id')
        
        if not endpoint_id:
            raise CommandError('--id is required for updating endpoints')
        
        try:
            endpoint = APIEndpoint.objects.get(id=endpoint_id)
        except APIEndpoint.DoesNotExist:
            raise CommandError(f'API endpoint with ID {endpoint_id} not found')
        
        # Update fields if provided
        if options.get('name'):
            endpoint.name = options['name']
        if options.get('url'):
            endpoint.url = options['url']
        if options.get('domain') is not None:
            endpoint.source_domain = options['domain']
        if options.get('priority') is not None:
            endpoint.priority = options['priority']
        if options.get('active'):
            endpoint.is_active = True
        if options.get('inactive'):
            endpoint.is_active = False
        
        endpoint.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated API endpoint: {endpoint.name}')
        )

    def delete_endpoint(self, options):
        """Delete an API endpoint"""
        endpoint_id = options.get('id')
        
        if not endpoint_id:
            raise CommandError('--id is required for deleting endpoints')
        
        try:
            endpoint = APIEndpoint.objects.get(id=endpoint_id)
            name = endpoint.name
            endpoint.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted API endpoint: {name}')
            )
            
        except APIEndpoint.DoesNotExist:
            raise CommandError(f'API endpoint with ID {endpoint_id} not found')

    def test_endpoint(self, options):
        """Test an API endpoint"""
        endpoint_id = options.get('id')
        
        if endpoint_id:
            try:
                endpoint = APIEndpoint.objects.get(id=endpoint_id)
                self._test_single_endpoint(endpoint)
            except APIEndpoint.DoesNotExist:
                raise CommandError(f'API endpoint with ID {endpoint_id} not found')
        else:
            # Test all active endpoints
            endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
            
            if not endpoints:
                self.stdout.write(self.style.WARNING('No active endpoints to test.'))
                return
            
            self.stdout.write(f'Testing {endpoints.count()} active endpoints...')
            
            for endpoint in endpoints:
                self._test_single_endpoint(endpoint)

    def _test_single_endpoint(self, endpoint):
        """Test a single API endpoint"""
        self.stdout.write(f'\nTesting endpoint: {endpoint.name} ({endpoint.url})')
        
        try:
            # Test basic connectivity
            test_url = f"{endpoint.url.rstrip('/')}/anime-terbaru"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {endpoint.name} is working (Status: {response.status_code})')
                )
                
                # Update success count
                endpoint.success_count += 1
                endpoint.save()
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ {endpoint.name} returned status {response.status_code}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ {endpoint.name} failed: {e}')
            )

    def set_priority(self, options):
        """Set priority for an API endpoint"""
        endpoint_id = options.get('id')
        priority = options.get('priority')
        
        if not endpoint_id or priority is None:
            raise CommandError('--id and --priority are required for setting priority')
        
        try:
            endpoint = APIEndpoint.objects.get(id=endpoint_id)
            endpoint.priority = priority
            endpoint.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set priority {priority} for endpoint: {endpoint.name}')
            )
            
        except APIEndpoint.DoesNotExist:
            raise CommandError(f'API endpoint with ID {endpoint_id} not found') 