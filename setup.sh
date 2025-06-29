#!/bin/bash

# Buildship FastAPI Development Environment Setup Script

set -e  # Exit on any error

echo "🚀 Setting up Buildship FastAPI development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is available
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Found Python 3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VERSION" > "3.10" ]]; then
            PYTHON_CMD="python3"
            print_success "Found Python $PYTHON_VERSION"
        else
            print_error "Python 3.11+ is required. Found Python $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3.11+ is not installed"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created at venv/"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    venv/bin/pip install --upgrade pip
    
    # Install requirements
    venv/bin/pip install -r requirements.txt
    
    print_success "Dependencies installed successfully!"
}

# Setup environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_success "Created .env file from env.example"
            print_warning "Please edit .env file with your database credentials"
        else
            print_warning "No env.example found. You may need to create .env manually"
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Start database and initialize
init_database() {
    print_status "Setting up database..."
    
    # Check if Docker is running
    if docker info > /dev/null 2>&1; then
        print_status "Docker is available. Starting database with Docker..."
        
        # Start PostgreSQL database
        docker-compose up -d postgres
        
        # Wait for database to be ready
        print_status "Waiting for database to be ready..."
        sleep 15
        
        # Check if database is accessible
        print_status "Checking database connection..."
        if docker-compose exec -T postgres pg_isready -U buildship_user -d buildship > /dev/null 2>&1; then
            print_success "Database is ready!"
        else
            print_warning "Database might not be fully ready, but continuing..."
        fi
        
        # Initialize database tables
        print_status "Creating database tables..."
        venv/bin/python -c "from app.database import init_db; init_db(); print('Database tables created successfully!')"
        print_success "Database initialized successfully!"
        
        # Start Redis if available
        print_status "Starting Redis..."
        docker-compose up -d redis
        
    else
        print_warning "Docker not available. Please ensure PostgreSQL is running and run:"
        echo "  make db-init"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests to verify setup..."
    
    venv/bin/python -m pytest tests/unit/ -v --tb=short
    print_success "Unit tests passed!"
}

# Main setup function
main() {
    echo "=========================================="
    echo "Buildship FastAPI Development Setup"
    echo "=========================================="
    
    check_python
    create_venv
    install_dependencies
    setup_env
    init_database
    run_tests
    
    echo ""
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Start the development server:"
    echo "   make dev"
    echo ""
    echo "3. Access the application:"
    echo "   - API: http://localhost:8000"
    echo "   - Documentation: http://localhost:8000/docs"
    echo "   - pgAdmin: http://localhost:5050"
    echo ""
    echo "4. Run tests:"
    echo "   make test"
    echo ""
    echo "5. View available commands:"
    echo "   make help"
    echo ""
    echo "6. To stop all services:"
    echo "   make docker-stop"
    echo ""
}

# Run main function
main "$@" 