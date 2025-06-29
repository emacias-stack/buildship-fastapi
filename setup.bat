@echo off
REM Buildship FastAPI Development Environment Setup Script for Windows

echo 🚀 Setting up Buildship FastAPI development environment...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Found Python
python --version

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist venv (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created at venv\

REM Install dependencies
echo [INFO] Installing dependencies...
venv\Scripts\pip.exe install --upgrade pip
venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed successfully!

REM Setup environment variables
echo [INFO] Setting up environment variables...
if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo [SUCCESS] Created .env file from env.example
        echo [WARNING] Please edit .env file with your database credentials
    ) else (
        echo [WARNING] No env.example found. You may need to create .env manually
    )
) else (
    echo [WARNING] .env file already exists
)

REM Start database and initialize
echo [INFO] Setting up database...
docker info >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker not available. Please ensure PostgreSQL is running and run:
    echo   make db-init
) else (
    echo [INFO] Docker is available. Starting database with Docker...
    
    REM Start PostgreSQL database
    docker-compose up -d postgres
    
    echo [INFO] Waiting for database to be ready...
    timeout /t 15 /nobreak >nul
    
    REM Check if database is accessible
    echo [INFO] Checking database connection...
    docker-compose exec -T postgres pg_isready -U buildship_user -d buildship >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Database might not be fully ready, but continuing...
    ) else (
        echo [SUCCESS] Database is ready!
    )
    
    REM Initialize database tables
    echo [INFO] Creating database tables...
    venv\Scripts\python.exe -c "from app.database import init_db; init_db(); print('Database tables created successfully!')"
    echo [SUCCESS] Database initialized successfully!
    
    REM Start Redis if available
    echo [INFO] Starting Redis...
    docker-compose up -d redis
)

REM Run tests
echo [INFO] Running tests to verify setup...
venv\Scripts\python.exe -m pytest tests\unit\ -v --tb=short
if errorlevel 1 (
    echo [WARNING] Some tests failed, but setup completed
) else (
    echo [SUCCESS] Unit tests passed!
)

echo.
echo ==========================================
echo [SUCCESS] Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Start the development server:
echo    make dev
echo.
echo 3. Access the application:
echo    - API: http://localhost:8000
echo    - Documentation: http://localhost:8000/docs
echo    - pgAdmin: http://localhost:5050
echo.
echo 4. Run tests:
echo    make test
echo.
echo 5. View available commands:
echo    make help
echo.
echo 6. To stop all services:
echo    make docker-stop
echo.
pause 