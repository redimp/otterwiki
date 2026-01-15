-- User table
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN NOT NULL DEFAULT 0,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    email_confirmed BOOLEAN NOT NULL DEFAULT 0,
    allow_read BOOLEAN NOT NULL DEFAULT 0,
    allow_write BOOLEAN NOT NULL DEFAULT 0,
    allow_upload BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- Preferences table
CREATE TABLE IF NOT EXISTS preferences (
    name TEXT PRIMARY KEY,
    value TEXT
);

-- Drafts table
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pagepath TEXT NOT NULL,
    revision TEXT NOT NULL,
    author_email TEXT NOT NULL,
    content TEXT,
    cursor_line INTEGER NOT NULL DEFAULT 0,
    cursor_ch INTEGER NOT NULL DEFAULT 0,
    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_drafts_pagepath ON drafts(pagepath);

-- Cache table
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT,
    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(key);
