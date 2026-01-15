#!/bin/bash
# Quick setup script for Otterwiki Rust
# This script creates the database and initializes the git repository

set -e

echo "🦦 Otterwiki Rust - Quick Setup"
echo "================================"

# Check if binary exists
if [ ! -f "target/release/otterwiki-rust" ]; then
    echo "❌ Binary not found. Please build first with: cargo build --release"
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p app-data/repository

# Initialize git repository
if [ ! -d "app-data/repository/.git" ]; then
    echo "🔧 Initializing git repository..."
    cd app-data/repository
    git init
    git config user.name "Otterwiki"
    git config user.email "otterwiki@localhost"
    cd ../..
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Create settings.toml if it doesn't exist
if [ ! -f "settings.toml" ]; then
    echo "⚙️  Creating settings.toml..."
    cat > settings.toml << 'EOF'
# Otterwiki Rust Configuration

port = 8080
debug = false

# IMPORTANT: Change this to a random string!
secret_key = "CHANGE_ME_TO_A_RANDOM_STRING_AT_LEAST_16_CHARS"

repository = "app-data/repository"
database_url = "sqlite://app-data/otterwiki.db"

site_name = "An Otter Wiki"
site_lang = "en"

read_access = "ANONYMOUS"
write_access = "ANONYMOUS"
attachment_access = "ANONYMOUS"

auto_approval = true
disable_registration = false
email_needs_confirmation = true
retain_page_name_case = false

commit_message = "REQUIRED"
robots_txt = "allow"
EOF
    echo "✅ Created settings.toml"
    echo "⚠️  IMPORTANT: Edit settings.toml and set a secure secret_key!"
else
    echo "✅ settings.toml already exists"
fi

# Create database (it will be created automatically on first run)
echo ""
echo "📊 Database will be created automatically at: app-data/otterwiki.db"
echo "   (Created when you first run the application)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit settings.toml and set a secure secret_key"
echo "2. Run: ./target/release/otterwiki-rust"
echo "3. Open http://localhost:8080 in your browser"
echo ""
echo "Happy wiki-ing! 🦦"
