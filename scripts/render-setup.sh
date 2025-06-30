#!/bin/bash

# Render Deployment Setup Script

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

print_status "Render Deployment Setup"
echo "================================"

# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

print_status "Generated Environment Variables for Render:"
echo ""
echo "Required Variables:"
echo "=================="
echo "DATABASE_URL=postgresql://fastapi_sample_user:YOUR_PASSWORD@YOUR_HOST:5432/buildship"
echo "SECRET_KEY=$SECRET_KEY"
echo ""
echo "Optional Variables:"
echo "=================="
echo "DEBUG=false"
echo "LOG_LEVEL=INFO"
echo "APP_NAME=Buildship FastAPI"
echo "APP_VERSION=1.0.0"
echo "HOST=0.0.0.0"
echo "PORT=8000"
echo "WORKERS=4"
echo "DATABASE_POOL_SIZE=10"
echo "DATABASE_MAX_OVERFLOW=20"
echo "ALGORITHM=HS256"
echo "ACCESS_TOKEN_EXPIRE_MINUTES=30"
echo "ENABLE_METRICS=true"
echo "METRICS_PORT=9090"
echo ""

print_status "Render Setup Instructions:"
echo "1. Create a PostgreSQL database in Render"
echo "2. Create a Web Service and connect your GitHub repo"
echo "3. Set the environment variables above in your Web Service"
echo "4. Set build command: pip install -r requirements.txt"
echo "5. Set start command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo ""

print_warning "Important Notes:"
echo "- Replace YOUR_PASSWORD with your actual PostgreSQL password"
echo "- Replace YOUR_HOST with your PostgreSQL host from Render"
echo "- The SECRET_KEY above is generated for you - use it!"
echo "- Set DEBUG=false for production"
echo ""

print_success "Setup complete! Copy the environment variables above to Render." 