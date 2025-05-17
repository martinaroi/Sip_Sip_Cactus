-- CREATE ROLE plant_user WITH LOGIN PASSWORD 'password';

-- -- Grant database connection permission
-- GRANT CONNECT ON DATABASE postgres TO plant_user;
-- GRANT USAGE ON SCHEMA pg_catalog TO plant_user;

-- Grant schema permissions
GRANT USAGE, CREATE ON SCHEMA public TO plant_user;

-- Grant table and sequence permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO plant_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO plant_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO plant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO plant_user;