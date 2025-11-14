-- Create Keycloak schema
CREATE SCHEMA IF NOT EXISTS keycloak;

-- Grant privileges to the g3wsuite user on keycloak schema
GRANT ALL PRIVILEGES ON SCHEMA keycloak TO ${G3WSUITE_POSTGRES_USER_LOCAL};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA keycloak TO ${G3WSUITE_POSTGRES_USER_LOCAL};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA keycloak TO ${G3WSUITE_POSTGRES_USER_LOCAL};

-- Set default privileges for future objects in keycloak schema
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak GRANT ALL PRIVILEGES ON TABLES TO ${G3WSUITE_POSTGRES_USER_LOCAL};
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak GRANT ALL PRIVILEGES ON SEQUENCES TO ${G3WSUITE_POSTGRES_USER_LOCAL};

-- Set search path to include keycloak schema
-- This allows Keycloak to work with the schema without explicitly specifying it
