# Database Backup Scripts

This directory contains database backup and restore utilities for the myapp project.

## Usage

### Python Script (Cross-platform)

The `db_backup.py` script works on Windows, Mac, and Linux.

#### Backup

```bash
# Create a backup from local environment
python scripts/db_backup.py backup local

# Create a backup with custom filename
python scripts/db_backup.py backup local my_backup.dump

# Create a backup from production environment
python scripts/db_backup.py backup production
```

#### Restore

```bash
# Restore from backup (uses default database from env file)
python scripts/db_backup.py restore local production_db.dump

# Restore to a different database
python scripts/db_backup.py restore local production_db.dump wraft
```

### Makefile Targets

#### Backup

```bash
# Backup local environment
make backup-local

# Backup production environment
make backup-production
```

#### Restore

```bash
# Restore from backup (uses default database)
make restore-local BACKUP_FILE=production_db.dump

# Restore to a different database
make restore-local BACKUP_FILE=production_db.dump TARGET_DB=wraft
```

## How It Works

1. **Backup**: Creates a PostgreSQL custom format dump using `pg_dump` from the postgres container
2. **Restore**: 
   - Copies the backup file to the postgres container
   - Uses `pg_restore` to restore the database
   - Automatically cleans up the temporary file in the container

## Backup File Location

Backups are stored in the `backups/` directory at the project root. Files are automatically named with timestamps unless you specify a custom name.

## Requirements

- Docker and Docker Compose must be installed
- The postgres service must be running in the target environment
- Python 3.6+ (for the Python script)

