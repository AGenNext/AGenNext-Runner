#!/bin/bash
set -e
echo "=== Initialising secondary databases ==="
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" << EOSQL

DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'langfuse') THEN
    CREATE USER langfuse WITH PASSWORD '$LANGFUSE_DB_PASSWORD';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE langfuse' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
ALTER DATABASE langfuse OWNER TO langfuse;
GRANT ALL PRIVILEGES ON DATABASE langfuse TO langfuse;

DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lago') THEN
    CREATE USER lago WITH PASSWORD '$LAGO_DB_PASSWORD';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE lago' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lago')\gexec
ALTER DATABASE lago OWNER TO lago;
GRANT ALL PRIVILEGES ON DATABASE lago TO lago;

DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keycloak') THEN
    CREATE USER keycloak WITH PASSWORD '$KEYCLOAK_DB_PASSWORD';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE keycloak' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec
ALTER DATABASE keycloak OWNER TO keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;

DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keystone') THEN
    CREATE USER keystone WITH PASSWORD '$KEYSTONE_DB_PASSWORD';
  END IF;
END \$\$;
SELECT 'CREATE DATABASE keystone' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keystone')\gexec
ALTER DATABASE keystone OWNER TO keystone;
GRANT ALL PRIVILEGES ON DATABASE keystone TO keystone;

EOSQL

for db in langfuse lago keycloak keystone; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" -c "GRANT ALL ON SCHEMA public TO $db; ALTER SCHEMA public OWNER TO $db;"
done

echo "=== All secondary databases created ==="
