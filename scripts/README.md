# Scripts Directory

This directory contains runtime scripts for the Sync Scribe Studio API project.

## Purpose
Store executable scripts that support various runtime operations, including:
- Database migrations
- Data processing utilities
- Deployment scripts
- Maintenance tasks
- Helper scripts for development and production

## Naming Conventions
- Use descriptive names with underscores: `migrate_database.py`, `backup_data.sh`
- Add appropriate file extensions: `.py` for Python, `.sh` for shell scripts
- Group related scripts with common prefixes: `db_*.py`, `deploy_*.sh`

## Best Practices
- Include clear documentation in each script
- Add usage examples in script headers
- Make scripts idempotent where possible
- Handle errors gracefully with proper logging
