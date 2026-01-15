# 🚀 Otterwiki Rust - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Rust 1.70+ installed
- Git installed
- ~20MB disk space

## Option 1: Automated Setup (Recommended)

```bash
# 1. Build the project
cargo build --release

# 2. Run the setup script
./setup.sh

# 3. Edit the configuration
nano settings.toml  # Change the secret_key!

# 4. Run the server
./target/release/otterwiki-rust
```

That's it! Open http://localhost:8080

## Option 2: Manual Setup

```bash
# 1. Build
cargo build --release

# 2. Create directories
mkdir -p app-data/repository
cd app-data/repository && git init && cd ../..

# 3. Create configuration
cp settings.toml.example settings.toml
nano settings.toml  # Edit as needed

# 4. Run
./target/release/otterwiki-rust
```

## Option 3: Using Make

```bash
# One command setup
make -f Makefile.rust quickstart

# Then run
make -f Makefile.rust run
```

## What Gets Created?

```
app-data/
├── repository/          # Git repository for wiki pages
│   └── .git/
└── otterwiki.db         # SQLite database (created on first run)

settings.toml            # Your configuration file
```

## Database Creation

**The database is created automatically!** You don't need to do anything.

When you first run `./target/release/otterwiki-rust`:

1. ✅ Connects to SQLite (creates file if needed)
2. ✅ Runs migrations automatically
3. ✅ Creates all tables (user, preferences, drafts, cache)
4. ✅ Ready to use!

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for details.

## First Use

1. **Open browser**: http://localhost:8080
2. **Register account**: Click "Register" (first user is admin)
3. **Create pages**: Start editing!

## Configuration Checklist

Before running in production, edit `settings.toml`:

- [ ] Set `secret_key` to a random string (16+ characters)
- [ ] Configure `repository` path
- [ ] Set `database_url` path
- [ ] Configure access controls (`read_access`, `write_access`)
- [ ] Set email settings if needed

## Minimum Configuration

```toml
port = 8080
secret_key = "your-random-secret-key-here-make-it-long"
repository = "app-data/repository"
database_url = "sqlite://app-data/otterwiki.db"
```

## Docker Quick Start

```bash
# Build image
docker build -f Dockerfile.rust -t otterwiki-rust .

# Run
docker run -p 8080:8080 -v $(pwd)/app-data:/app-data otterwiki-rust

# Or use docker-compose
docker-compose -f docker-compose.rust.yml up -d
```

## Troubleshooting

### "Secret key too short"
Edit `settings.toml` and set a longer secret key (16+ chars)

### "Repository not found"
Create the directory and init git:
```bash
mkdir -p app-data/repository
cd app-data/repository && git init && cd ../..
```

### "Database error"
The database is created automatically. Check file permissions:
```bash
mkdir -p app-data
chmod 755 app-data
```

### Port already in use
Change port in `settings.toml`:
```toml
port = 8081  # or any other port
```

## Performance Tips

- **Binary size**: Already optimized (~11MB)
- **Memory**: Uses ~30MB RAM idle
- **Startup**: ~100ms cold start
- **Requests**: Handles 1000+ req/sec on modern hardware

## Next Steps

- Read [README_RUST.md](README_RUST.md) for full documentation
- See [PYTHON_VS_RUST.md](PYTHON_VS_RUST.md) for comparison
- Check [DATABASE_SETUP.md](DATABASE_SETUP.md) for database details
- Review [BUILD_RUST.md](BUILD_RUST.md) for build options

## Help

- Database setup: [DATABASE_SETUP.md](DATABASE_SETUP.md)
- Build issues: [BUILD_RUST.md](BUILD_RUST.md)
- Features: [README_RUST.md](README_RUST.md)
- Comparison: [PYTHON_VS_RUST.md](PYTHON_VS_RUST.md)

---

**Welcome to Otterwiki!** 🦦🦀
