-- Initialize PostgreSQL database for Buildship FastAPI application

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE buildship TO fastapi_sample_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO fastapi_sample_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fastapi_sample_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fastapi_sample_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fastapi_sample_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fastapi_sample_user; 