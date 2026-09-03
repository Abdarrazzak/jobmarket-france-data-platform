-- Replace placeholders locally before execution.
-- Never commit a real PostgreSQL username or password in this file.
CREATE USER <utilisateur_postgresql_local> WITH PASSWORD '<mot_de_passe_non_versionne>';
CREATE DATABASE jobmarket OWNER <utilisateur_postgresql_local>;
GRANT ALL PRIVILEGES ON DATABASE jobmarket TO <utilisateur_postgresql_local>;
