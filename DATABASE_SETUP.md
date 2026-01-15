# Creating the SQLite Database for Otterwiki (Rust)

The Rust version of Otterwiki uses **SQLx** with automatic migrations. The database is created automatically when you first run the application.

## 🚀 Quick Start (Automatic)

The **easiest way** is to just run the application - it will create the database automatically:

```bash
# 1. Make sure your settings.toml is configured
# database_url = "sqlite://otterwiki.db"  # or absolute path

# 2. Run the application
./target/release/otterwiki-rust
```

The application will:
1. Create `otterwiki.db` file automatically
2. Run all migrations from `migrations/` directory
3. Set up all tables (user, preferences, drafts, cache)
4. Be ready to use!

## 📋 Manual Creation (Optional)

If you want to create the database manually before running:

### Method 1: Using SQLite CLI

```bash
# Install sqlite3 if not already installed
# Ubuntu/Debian: sudo apt install sqlite3
# macOS: brew install sqlite3

# Create the database and run the migration
sqlite3 otterwiki.db < migrations/20240101000000_initial.sql

# Verify tables were created
sqlite3 otterwiki.db ".tables"
# Should show: cache  drafts  preferences  user
```

### Method 2: Using sqlx-cli (Recommended for Development)

```bash
# Install sqlx-cli
cargo install sqlx-cli --no-default-features --features sqlite

# Create the database (from project root)
sqlx database create

# Run migrations
sqlx migrate run

# Verify
sqlx database status
```

## 🗄️ Database Schema

The database includes 4 tables:

### 1. **user** - User accounts
```sql
- id (PRIMARY KEY)
- name
- email (UNIQUE)
- password_hash
- first_seen, last_seen (timestamps)
- is_approved, is_admin, email_confirmed (booleans)
- allow_read, allow_write, allow_upload (permissions)
```

### 2. **preferences** - Application settings
```sql
- name (PRIMARY KEY)
- value
```

### 3. **drafts** - Auto-saved page drafts
```sql
- id (PRIMARY KEY)
- pagepath, revision
- author_email
- content
- cursor_line, cursor_ch
- datetime
```

### 4. **cache** - Cached data
```sql
- key (PRIMARY KEY)
- value
- datetime
```

## 🔧 Configuration

### In settings.toml
```toml
# Relative path (creates in current directory)
database_url = "sqlite://otterwiki.db"

# Or absolute path
database_url = "sqlite:///app-data/otterwiki.db"

# Or in-memory (for testing)
database_url = "sqlite::memory:"
```

### Via Environment Variable
```bash
export OTTERWIKI_DATABASE_URL="sqlite://otterwiki.db"
./target/release/otterwiki-rust
```

## 🐳 Docker Setup

With Docker, the database is created automatically in the volume:

```yaml
services:
  otterwiki-rust:
    image: otterwiki-rust
    volumes:
      - ./app-data:/app-data
    environment:
      - OTTERWIKI_DATABASE_URL=sqlite:///app-data/otterwiki.db
```

The database will be at `./app-data/otterwiki.db` on your host.

## 🔍 Verifying the Database

After creation, verify it works:

```bash
# Using sqlite3
sqlite3 otterwiki.db ".schema user"

# Using sqlx-cli
sqlx database status

# Or just check the file exists
ls -lh otterwiki.db
```

## 🔄 Migrations

The Rust version uses SQLx migrations located in `migrations/`:

```
migrations/
└── 20240101000000_initial.sql    # Initial schema
```

To add new migrations:

```bash
# Create a new migration
sqlx migrate add <name>

# Edit the generated file in migrations/
# Then run:
sqlx migrate run
```

## 🎯 Common Locations

Depending on your setup:

| Setup | Database Location |
|-------|------------------|
| Development | `./otterwiki.db` (project root) |
| Docker | `/app-data/otterwiki.db` (in container) |
| Production | `/var/lib/otterwiki/otterwiki.db` (recommended) |
| Testing | `sqlite::memory:` (RAM only) |

## ⚠️ Important Notes

1. **Automatic Creation**: The Rust version automatically creates and migrates the database on startup
2. **Compatible**: The schema is identical to the Python version - you can use an existing database
3. **Migrations**: SQLx verifies migrations at compile time for safety
4. **File Permissions**: Make sure the directory is writable by the application
5. **Backup**: Always backup before migrations: `cp otterwiki.db otterwiki.db.backup`

## 🔒 Migration from Python Version

If you have an existing Python Otterwiki database:

```bash
# It should just work! Same schema.
# Just point to it:
database_url = "sqlite:///path/to/existing/otterwiki.db"

# The Rust version will recognize the existing schema
# and only run any new migrations if needed
```

## 🆘 Troubleshooting

### "Unable to open database file"
```bash
# Check directory is writable
chmod 755 $(dirname otterwiki.db)

# Or use absolute path
database_url = "sqlite:///absolute/path/to/otterwiki.db"
```

### "Database is locked"
```bash
# Another process has the database open
# Check for other instances:
lsof otterwiki.db

# Or just restart
```

### "Migration failed"
```bash
# Check migration status
sqlx migrate info

# Reset (CAUTION: destroys data)
sqlx database reset
```

## 📝 Summary

**You don't need to do anything!** Just run the application:

```bash
./target/release/otterwiki-rust
```

The database will be created automatically with all tables and indexes. 🎉
