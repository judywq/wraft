#!/usr/bin/env python3
"""
Database backup and restore script for myapp project.
Works on Windows, Mac, and Linux.

Usage:
    python scripts/db_backup.py backup <environment> [output_file]
    python scripts/db_backup.py restore <environment> [backup_file] [target_db]

If backup_file is not provided for restore, an interactive menu will be shown
to select from available backup files.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent.resolve()


def get_docker_compose_file(environment):
    """Get the docker-compose file path for the given environment."""
    project_root = get_project_root()
    compose_file = project_root / f"docker-compose.{environment}.yml"
    if not compose_file.exists():
        print(f"Error: docker-compose.{environment}.yml not found", file=sys.stderr)
        sys.exit(1)
    return compose_file


def get_env_file(environment):
    """Get the environment file path for database configuration."""
    project_root = get_project_root()
    env_file = project_root / ".envs" / f".{environment}" / ".django"
    if not env_file.exists():
        print(f"Error: .envs/.{environment}/.django not found", file=sys.stderr)
        sys.exit(1)
    return env_file


def parse_env_file(env_file):
    """Parse environment file and return database configuration."""
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                config[key] = value
    return config


def get_backup_dir():
    """Get the backups directory path."""
    project_root = get_project_root()
    backup_dir = project_root / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def run_docker_compose(compose_file, command, service=None, args=None):
    """Run a docker compose command."""
    cmd = ["docker", "compose", "-f", str(compose_file)]
    if service:
        cmd.extend(command)
        cmd.append(service)
        if args:
            cmd.extend(args)
    else:
        cmd.extend(command)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running docker compose command: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result


def backup_database(environment, output_file=None):
    """Create a database backup."""
    compose_file = get_docker_compose_file(environment)
    env_file = get_env_file(environment)
    config = parse_env_file(env_file)

    db_name = config.get("POSTGRES_DB", "myapp")
    db_user = config.get("POSTGRES_USER", "postgres")

    backup_dir = get_backup_dir()

    if output_file:
        if os.path.isabs(output_file):
            backup_path = Path(output_file)
        else:
            backup_path = backup_dir / output_file
    else:
        timestamp = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
        backup_path = backup_dir / f"{environment}_db_{timestamp}.dump"

    # Ensure the backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating backup of database '{db_name}' from {environment} environment...")
    print(f"Backup file: {backup_path}")

    # Create backup using pg_dump
    cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "pg_dump", "-U", db_user, "-Fc", db_name
    ]

    try:
        with open(backup_path, 'wb') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)

        file_size = backup_path.stat().st_size
        print(f"✓ Backup created successfully! Size: {file_size / 1024 / 1024:.2f} MB")
        return str(backup_path)
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e.stderr.decode()}", file=sys.stderr)
        if backup_path.exists():
            backup_path.unlink()
        sys.exit(1)


def clean_database(compose_file, db_user, db_name):
    """Drop and recreate the database to ensure a clean state."""
    print("Cleaning database (dropping and recreating)...")

    # Get the default database name (usually 'postgres') to connect to
    default_db = "postgres"

    # Quote database name for SQL safety (escape single quotes and wrap in quotes)
    # For PostgreSQL identifiers, we use double quotes
    db_name_quoted = f'"{db_name}"'
    # For string literals in SQL, we use single quotes and escape any single quotes
    db_name_sql_literal = db_name.replace("'", "''")

    # First, terminate all connections to the target database
    print("Terminating existing connections...")
    terminate_cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "psql", "-U", db_user, "-d", default_db,
        "-c", f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name_sql_literal}' AND pid <> pg_backend_pid();"
    ]

    try:
        subprocess.run(terminate_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        # Ignore errors - connections might not exist
        pass

    # Drop the database
    print(f"Dropping database '{db_name}'...")
    drop_cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "psql", "-U", db_user, "-d", default_db,
        "-c", f"DROP DATABASE IF EXISTS {db_name_quoted};"
    ]

    try:
        subprocess.run(drop_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Error dropping database: {e.stderr if e.stderr else e.stdout}", file=sys.stderr)
        # Continue anyway - might not exist

    # Recreate the database
    print(f"Creating database '{db_name}'...")
    create_cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "psql", "-U", db_user, "-d", default_db,
        "-c", f"CREATE DATABASE {db_name_quoted};"
    ]

    try:
        subprocess.run(create_cmd, check=True, capture_output=True, text=True)
        print("✓ Database cleaned and recreated successfully!")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout if e.stdout else str(e)
        print(f"Error recreating database: {error_msg}", file=sys.stderr)
        sys.exit(1)


def restore_via_stdin(compose_file, backup_path, db_user, db_name):
    """Restore database by piping backup directly to pg_restore."""
    print("Restoring database via stdin...")
    cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "pg_restore", "-U", db_user, "-d", db_name, "--no-owner", "--no-acl", "-"
    ]

    try:
        with open(backup_path, 'rb') as f:
            result = subprocess.run(cmd, stdin=f, check=True, capture_output=True)
        print("✓ Database restored successfully!")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else e.stdout.decode() if e.stdout else str(e)
        print(f"Error restoring database: {error_msg}", file=sys.stderr)
        sys.exit(1)


def list_backup_files():
    """List all backup files in the backup directory."""
    backup_dir = get_backup_dir()
    backup_files = sorted(
        [f for f in backup_dir.iterdir() if f.is_file() and f.suffix == '.dump'],
        key=lambda x: x.stat().st_mtime,
        reverse=True  # Most recent first
    )
    return backup_files


def select_backup_file():
    """Display backup files and let user select one."""
    backup_files = list_backup_files()

    if not backup_files:
        print("No backup files found in the backups directory.", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable backup files:")
    print("-" * 60)
    for idx, backup_file in enumerate(backup_files, 1):
        file_size = backup_file.stat().st_size
        file_size_mb = file_size / 1024 / 1024
        mod_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  {idx}. {backup_file.name}")
        print(f"     Size: {file_size_mb:.2f} MB | Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    while True:
        try:
            choice = input(f"\nSelect a backup file (1-{len(backup_files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                print("Restore cancelled.")
                sys.exit(0)

            file_idx = int(choice) - 1
            if 0 <= file_idx < len(backup_files):
                selected_file = backup_files[file_idx]
                return selected_file
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(backup_files)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\nRestore cancelled.")
            sys.exit(0)


def confirm_restore(backup_path, db_name):
    """Ask user to confirm the restore operation."""
    print(f"\n⚠️  WARNING: This will OVERWRITE the existing database '{db_name}'!")
    print(f"   Backup file: {backup_path.name}")
    print(f"   Full path: {backup_path}")

    while True:
        try:
            confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                return True
            elif confirm in ('no', 'n'):
                print("Restore cancelled.")
                return False
            else:
                print("Please enter 'yes' or 'no'.")
        except KeyboardInterrupt:
            print("\nRestore cancelled.")
            return False


def restore_database(environment, backup_file, target_db=None):
    """Restore a database from a backup."""
    compose_file = get_docker_compose_file(environment)
    env_file = get_env_file(environment)
    config = parse_env_file(env_file)

    db_name = target_db or config.get("POSTGRES_DB", "myapp")
    db_user = config.get("POSTGRES_USER", "postgres")

    # If backup_file is not provided, let user select from list
    if not backup_file or not backup_file.strip():
        backup_path = select_backup_file()
    else:
        # Resolve backup file path
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = get_backup_dir() / backup_file

        if not backup_path.exists():
            print(f"Error: Backup file not found: {backup_path}", file=sys.stderr)
            sys.exit(1)

    # Ask for confirmation
    if not confirm_restore(backup_path, db_name):
        sys.exit(0)

    print(f"\nRestoring database '{db_name}' from backup: {backup_path}")

    # Clean the database first (drop and recreate)
    clean_database(compose_file, db_user, db_name)

    # Try docker compose cp first (Docker Compose v2.18+)
    # This is the cleanest approach and works cross-platform
    try:
        print("Copying backup file to container using docker compose cp...")
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "cp", str(backup_path), "postgres:/tmp/restore.dump"],
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: get container name and use docker cp
        print("docker compose cp not available, using docker cp...")
        container_name = None

        # Try to get container name from docker compose ps
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "ps", "-q", "postgres"],
                capture_output=True,
                text=True,
                check=True
            )
            container_id = result.stdout.strip()
            if container_id:
                # Get container name from ID
                result = subprocess.run(
                    ["docker", "inspect", "--format={{.Name}}", container_id],
                    capture_output=True,
                    text=True,
                    check=True
                )
                container_name = result.stdout.strip().lstrip('/')
        except subprocess.CalledProcessError:
            pass

        if not container_name:
            # Last resort: try stdin method
            print("Could not determine container name. Using stdin method...")
            restore_via_stdin(compose_file, backup_path, db_user, db_name)
            return

        print(f"Copying backup file to container '{container_name}'...")
        try:
            subprocess.run(
                ["docker", "cp", str(backup_path), f"{container_name}:/tmp/restore.dump"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error copying backup to container: {e}", file=sys.stderr)
            print("Trying alternative method: using stdin for pg_restore...", file=sys.stderr)
            restore_via_stdin(compose_file, backup_path, db_user, db_name)
            return

    # Restore database (no need for -c since we cleaned it already)
    print(f"Restoring database...")
    cmd = [
        "docker", "compose", "-f", str(compose_file),
        "exec", "-T", "postgres",
        "pg_restore", "-U", db_user, "-d", db_name, "--no-owner", "--no-acl", "/tmp/restore.dump"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Database restored successfully!")

        # Clean up backup file from container
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file),
                 "exec", "-T", "postgres", "rm", "/tmp/restore.dump"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            pass  # Ignore cleanup errors

    except subprocess.CalledProcessError as e:
        print(f"Error restoring database: {e.stderr if e.stderr else e.stdout}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Database backup and restore utility for myapp project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a backup from local environment
  python scripts/db_backup.py backup local

  # Create a backup with custom filename
  python scripts/db_backup.py backup local my_backup.dump

  # Restore from backup (interactive selection if backup_file not provided)
  python scripts/db_backup.py restore local

  # Restore from specific backup file
  python scripts/db_backup.py restore local my_backup.dump

  # Restore to a different database
  python scripts/db_backup.py restore local my_backup.dump other_db_name
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create a database backup')
    backup_parser.add_argument('environment', choices=['local', 'production'], help='Environment to backup')
    backup_parser.add_argument('output_file', nargs='?', help='Output backup filename (optional)')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore a database from backup')
    restore_parser.add_argument('environment', choices=['local', 'production'], help='Environment to restore to')
    restore_parser.add_argument('backup_file', nargs='?', help='Backup file to restore from (optional, will show interactive menu if not provided)')
    restore_parser.add_argument('target_db', nargs='?', help='Target database name (optional, uses env default)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'backup':
        backup_database(args.environment, args.output_file)
    elif args.command == 'restore':
        # Handle empty backup_file (convert to None for interactive selection)
        backup_file = args.backup_file.strip() if (args.backup_file and args.backup_file.strip()) else None
        # Handle empty target_db (convert to None)
        target_db = args.target_db if (args.target_db and args.target_db.strip()) else None
        restore_database(args.environment, backup_file, target_db)


if __name__ == '__main__':
    main()

