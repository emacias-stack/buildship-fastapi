#!/bin/bash

# CI/CD Pipeline Local Runner
# This script runs the same checks locally that the CI pipeline runs

set -e  # Exit on any error

echo "🚀 Running CI/CD Pipeline Checks Locally"
echo "========================================"

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

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Not in a virtual environment. Please activate your virtual environment first."
    print_status "Run: source venv/bin/activate"
    exit 1
fi

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null; then
        print_error "pip is not installed"
        exit 1
    fi
    
    # Check pytest
    if ! python -c "import pytest" &> /dev/null; then
        print_error "pytest is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check flake8
    if ! command -v flake8 &> /dev/null; then
        print_error "flake8 is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check mypy
    if ! command -v mypy &> /dev/null; then
        print_error "mypy is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check black
    if ! command -v black &> /dev/null; then
        print_error "black is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check isort
    if ! command -v isort &> /dev/null; then
        print_error "isort is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check bandit
    if ! command -v bandit &> /dev/null; then
        print_error "bandit is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Run tests
run_tests() {
    print_status "Running unit and integration tests..."
    
    # Set test environment variables
    export DATABASE_URL="sqlite:///./test.db"
    export SECRET_KEY="test-secret-key-for-ci"
    export DEBUG="false"
    export LOG_LEVEL="INFO"
    
    # Run tests with coverage
    python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=90
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Tests failed!"
        exit 1
    fi
}

# Run code quality checks
run_code_quality() {
    print_status "Running code quality checks..."
    
    # Run linting
    print_status "Running flake8..."
    flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503 --count --show-source --statistics
    
    if [ $? -eq 0 ]; then
        print_success "Flake8 passed!"
    else
        print_error "Flake8 failed!"
        exit 1
    fi
    
    # Run type checking
    print_status "Running mypy..."
    mypy app/ --ignore-missing-imports
    
    if [ $? -eq 0 ]; then
        print_success "MyPy passed!"
    else
        print_error "MyPy failed!"
        exit 1
    fi
    
    # Check code formatting
    print_status "Checking code formatting..."
    black --check app/ tests/ --line-length=88
    
    if [ $? -eq 0 ]; then
        print_success "Black formatting check passed!"
    else
        print_error "Black formatting check failed! Run: make format"
        exit 1
    fi
    
    # Check import sorting
    print_status "Checking import sorting..."
    isort --check-only app/ tests/ --profile=black
    
    if [ $? -eq 0 ]; then
        print_success "Import sorting check passed!"
    else
        print_error "Import sorting check failed! Run: make format"
        exit 1
    fi
}

# Run security scan
run_security_scan() {
    print_status "Running security scan..."
    
    bandit -r app/ -f json -o bandit-report.json || true
    
    if [ -f bandit-report.json ]; then
        print_success "Security scan completed. Check bandit-report.json for details."
    else
        print_warning "Security scan completed with warnings."
    fi
}

# Run performance test (if k6 is available)
run_performance_test() {
    print_status "Checking for k6..."
    
    if command -v k6 &> /dev/null; then
        print_status "Running quick performance test..."
        
        # Start the application in background
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        APP_PID=$!
        
        # Wait for app to start
        sleep 5
        
        # Run quick performance test
        k6 run k6/quick-test.js --summary-export=perf-summary.json
        
        # Stop the application
        kill $APP_PID 2>/dev/null || true
        
        if [ -f perf-summary.json ]; then
            print_success "Performance test completed. Check perf-summary.json for details."
        else
            print_warning "Performance test completed with warnings."
        fi
    else
        print_warning "k6 not found. Skipping performance tests."
        print_status "Install k6: brew install k6 (macOS) or visit https://k6.io/docs/getting-started/installation/"
    fi
}

# Clean up
cleanup() {
    print_status "Cleaning up..."
    
    # Remove test database
    rm -f test.db
    
    # Remove test artifacts
    rm -f bandit-report.json perf-summary.json
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    echo ""
    print_status "Starting CI/CD pipeline checks..."
    echo ""
    
    check_dependencies
    echo ""
    
    run_tests
    echo ""
    
    run_code_quality
    echo ""
    
    run_security_scan
    echo ""
    
    # run_performance_test
    # echo ""
    
    cleanup
    echo ""
    
    print_success "🎉 All CI/CD checks passed! Your code is ready for deployment."
    echo ""
    print_status "Next steps:"
    print_status "1. Commit your changes"
    print_status "2. Push to trigger the full CI/CD pipeline"
    print_status "3. Create a pull request for review"
}

# Run main function
main "$@" 