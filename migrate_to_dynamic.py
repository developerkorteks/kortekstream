#!/usr/bin/env python
"""
Migration script untuk mengubah sistem dari hardcoded values ke dynamic system.
Script ini akan membantu mengidentifikasi dan memperbaiki hardcoded values yang tersisa.
"""

import os
import sys
import re
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from streamapp.models import APIEndpoint, SiteConfiguration
from streamapp.utils import clear_domain_cache, get_current_source_domain
import logging

logger = logging.getLogger(__name__)

def check_hardcoded_values():
    """
    Check untuk hardcoded values yang tersisa di codebase.
    """
    print("🔍 Checking for hardcoded values...")
    
    # Patterns untuk hardcoded values
    patterns = [
        r'v1\.samehadaku\.how',
        r'kortekstream\.online',
        r'humanmade\.my\.id',
        r'https://[^/]+\.com',
        r'http://[^/]+\.com',
    ]
    
    hardcoded_files = []
    
    # Scan semua file Python dan template
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip venv dan git
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith(('.py', '.html', '.js')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            hardcoded_files.append({
                                'file': file_path,
                                'pattern': pattern,
                                'matches': matches
                            })
                            
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return hardcoded_files

def setup_default_endpoints():
    """
    Setup default API endpoints jika belum ada.
    """
    print("🔧 Setting up default API endpoints...")
    
    try:
        # Check if endpoints exist
        if APIEndpoint.objects.count() == 0:
            print("No API endpoints found. Creating default endpoints...")
            
            # Create default endpoints
            endpoints = [
                {
                    'name': 'Gomunime Primary',
                    'url': 'http://localhost:8080/api/v1/',
                    'source_domain': 'gomunime.co',
                    'priority': 500,
                    'is_active': True
                }
            ]
            
            for endpoint_data in endpoints:
                endpoint = APIEndpoint.objects.create(**endpoint_data)
                print(f"✅ Created endpoint: {endpoint.name}")
                
        else:
            print(f"Found {APIEndpoint.objects.count()} existing endpoints")
            
    except Exception as e:
        print(f"❌ Error setting up endpoints: {e}")

def test_dynamic_system():
    """
    Test sistem dynamic yang baru.
    """
    print("🧪 Testing dynamic system...")
    
    try:
        # Test domain retrieval
        current_domain = get_current_source_domain()
        print(f"✅ Current source domain: {current_domain}")
        
        # Test API endpoint info
        from streamapp.utils import get_api_endpoint_info
        endpoint_info = get_api_endpoint_info()
        print(f"✅ Active endpoint: {endpoint_info['name']} ({endpoint_info['url']})")
        
        # Test URL building
        from streamapp.utils import build_dynamic_url
        test_url = build_dynamic_url("anime/one-piece/")
        print(f"✅ Dynamic URL built: {test_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing dynamic system: {e}")
        return False

def clear_all_caches():
    """
    Clear semua cache yang terkait dengan domain.
    """
    print("🧹 Clearing all caches...")
    
    try:
        clear_domain_cache()
        print("✅ Domain cache cleared")
        
        # Clear Django cache
        from django.core.cache import cache
        cache.clear()
        print("✅ Django cache cleared")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def update_site_configuration():
    """
    Update site configuration untuk mendukung dynamic system.
    """
    print("⚙️ Updating site configuration...")
    
    try:
        # Create or update site configuration
        configs = [
            {
                'key': 'default_source_domain',
                'value': 'gomunime.co',
                'description': 'Default source domain for fallback'
            },
            {
                'key': 'dynamic_api_enabled',
                'value': 'true',
                'description': 'Enable dynamic API system'
            }
        ]
        
        for config_data in configs:
            config, created = SiteConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults={
                    'name': config_data['key'].replace('_', ' ').title(),
                    'value': config_data['value'],
                    'description': config_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                print(f"✅ Created config: {config.key}")
            else:
                print(f"ℹ️ Config already exists: {config.key}")
                
    except Exception as e:
        print(f"❌ Error updating site configuration: {e}")

def generate_migration_report():
    """
    Generate laporan migrasi.
    """
    print("📊 Generating migration report...")
    
    report = {
        'total_endpoints': APIEndpoint.objects.count(),
        'active_endpoints': APIEndpoint.objects.filter(is_active=True).count(),
        'current_domain': get_current_source_domain(),
        'hardcoded_files': check_hardcoded_values()
    }
    
    print("\n" + "="*50)
    print("MIGRATION REPORT")
    print("="*50)
    print(f"Total API Endpoints: {report['total_endpoints']}")
    print(f"Active Endpoints: {report['active_endpoints']}")
    print(f"Current Source Domain: {report['current_domain']}")
    print(f"Files with hardcoded values: {len(report['hardcoded_files'])}")
    
    if report['hardcoded_files']:
        print("\nFiles with hardcoded values:")
        for file_info in report['hardcoded_files']:
            print(f"  - {file_info['file']}")
            print(f"    Pattern: {file_info['pattern']}")
            print(f"    Matches: {len(file_info['matches'])}")
    
    print("\n" + "="*50)
    
    return report

def main():
    """
    Main migration function.
    """
    print("🚀 Starting migration to dynamic system...")
    print("="*50)
    
    try:
        # Step 1: Setup default endpoints
        setup_default_endpoints()
        print()
        
        # Step 2: Update site configuration
        update_site_configuration()
        print()
        
        # Step 3: Clear caches
        clear_all_caches()
        print()
        
        # Step 4: Test dynamic system
        if test_dynamic_system():
            print("✅ Dynamic system is working correctly")
        else:
            print("❌ Dynamic system has issues")
        print()
        
        # Step 5: Generate report
        report = generate_migration_report()
        
        print("\n🎉 Migration completed!")
        print("\nNext steps:")
        print("1. Test your website with: python manage.py runserver")
        print("2. Add more API endpoints with: python manage.py manage_api_endpoints add")
        print("3. Monitor endpoints with: python manage.py manage_api_endpoints test")
        print("4. Check the DYNAMIC_API_SETUP.md file for detailed instructions")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 