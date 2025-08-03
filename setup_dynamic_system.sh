#!/bin/bash

# Dynamic API System Setup Script
# Script untuk setup dan mengelola sistem API dynamic

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHONPATH="$VENV_DIR/lib/python3.10/site-packages"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to activate virtual environment
activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found. Please create it first."
        exit 1
    fi
    
    export PYTHONPATH="$PYTHONPATH"
    print_status "Virtual environment activated"
}

# Function to run Django command
run_django() {
    activate_venv
    "$VENV_DIR/bin/python" manage.py "$@"
}

# Function to setup default endpoints
setup_default_endpoints() {
    print_header "Setting up default API endpoints"
    
    # Add Samehadaku endpoint
    run_django manage_api_endpoints add \
        --name "Samehadaku Primary" \
        --url "https://api.samehadaku.how/api/v1" \
        --domain "v1.samehadaku.how" \
        --priority 10 \
        --active
    
    # Add Otakudesu endpoint
    run_django manage_api_endpoints add \
        --name "Otakudesu Backup" \
        --url "https://api.otakudesu.com/api/v1" \
        --domain "otakudesu.com" \
        --priority 5 \
        --active
    
    # Add AnimeIndo endpoint
    run_django manage_api_endpoints add \
        --name "AnimeIndo Backup" \
        --url "https://api.animeindo.com/api/v1" \
        --domain "animeindo.com" \
        --priority 3 \
        --active
    
    print_status "Default endpoints added"
}

# Function to test all endpoints
test_endpoints() {
    print_header "Testing all API endpoints"
    run_django manage_api_endpoints test
}

# Function to show endpoint status
show_endpoints() {
    print_header "Current API endpoints"
    run_django manage_api_endpoints list
}

# Function to add new endpoint
add_endpoint() {
    if [ $# -lt 4 ]; then
        print_error "Usage: $0 add-endpoint <name> <url> <domain> <priority>"
        exit 1
    fi
    
    local name="$1"
    local url="$2"
    local domain="$3"
    local priority="$4"
    
    print_header "Adding new endpoint: $name"
    run_django manage_api_endpoints add \
        --name "$name" \
        --url "$url" \
        --domain "$domain" \
        --priority "$priority" \
        --active
}

# Function to update endpoint
update_endpoint() {
    if [ $# -lt 2 ]; then
        print_error "Usage: $0 update-endpoint <id> [--name <name>] [--url <url>] [--domain <domain>] [--priority <priority>]"
        exit 1
    fi
    
    local id="$1"
    shift
    
    print_header "Updating endpoint ID: $id"
    run_django manage_api_endpoints update --id "$id" "$@"
}

# Function to delete endpoint
delete_endpoint() {
    if [ $# -lt 1 ]; then
        print_error "Usage: $0 delete-endpoint <id>"
        exit 1
    fi
    
    local id="$1"
    print_header "Deleting endpoint ID: $id"
    run_django manage_api_endpoints delete --id "$id"
}

# Function to run migration
run_migration() {
    print_header "Running migration to dynamic system"
    activate_venv
    "$VENV_DIR/bin/python" migrate_to_dynamic.py
}

# Function to start development server
start_server() {
    print_header "Starting development server"
    activate_venv
    "$VENV_DIR/bin/python" manage.py runserver 0.0.0.0:8000
}

# Function to show help
show_help() {
    echo "Dynamic API System Management Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup              Setup default API endpoints"
    echo "  test               Test all API endpoints"
    echo "  list               Show all API endpoints"
    echo "  add-endpoint       Add new API endpoint"
    echo "  update-endpoint    Update existing API endpoint"
    echo "  delete-endpoint    Delete API endpoint"
    echo "  migrate            Run migration to dynamic system"
    echo "  server             Start development server"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 add-endpoint 'My API' 'https://api.example.com/v1' 'example.com' 5"
    echo "  $0 update-endpoint 1 --priority 10"
    echo "  $0 delete-endpoint 1"
    echo "  $0 test"
    echo "  $0 server"
}

# Main script logic
case "${1:-help}" in
    "setup")
        setup_default_endpoints
        ;;
    "test")
        test_endpoints
        ;;
    "list")
        show_endpoints
        ;;
    "add-endpoint")
        shift
        add_endpoint "$@"
        ;;
    "update-endpoint")
        shift
        update_endpoint "$@"
        ;;
    "delete-endpoint")
        shift
        delete_endpoint "$@"
        ;;
    "migrate")
        run_migration
        ;;
    "server")
        start_server
        ;;
    "help"|*)
        show_help
        ;;
esac 