#!/bin/bash

# Buildship FastAPI Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Get version information
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "dev")
MAJOR_MINOR=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' | sed 's/\.[0-9]*$//' || echo "dev")
GIT_COMMIT=$(git rev-parse --short HEAD)

print_status "Deployment Information:"
print_status "  Full Version: $VERSION"
print_status "  Major.Minor: $MAJOR_MINOR"
print_status "  Git Commit: $GIT_COMMIT"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create one from env.example"
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
required_vars=("POSTGRES_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_status "Starting deployment for version $MAJOR_MINOR..."

# Build and push Docker image
print_status "Building and pushing Docker image..."
make docker-push

# Deploy to production
print_status "Deploying to production..."
export MAJOR_MINOR=$MAJOR_MINOR
make docker-deploy

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check application health
print_status "Checking application health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Application is healthy!"
else
    print_error "Application health check failed"
    exit 1
fi

print_success "Deployment completed successfully!"
print_status "Application is available at: http://localhost:8000"
print_status "Health check: http://localhost:8000/health"
print_status "Deployed version: $MAJOR_MINOR" 