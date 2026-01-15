use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub name: String,
    pub email: String,
    pub password_hash: String,
    pub first_seen: DateTime<Utc>,
    pub last_seen: DateTime<Utc>,
    pub is_approved: bool,
    pub is_admin: bool,
    pub email_confirmed: bool,
    pub allow_read: bool,
    pub allow_write: bool,
    pub allow_upload: bool,
}

impl User {
    pub fn permissions_string(&self) -> String {
        let mut perms = String::new();
        if self.allow_read {
            perms.push('R');
        }
        if self.allow_write {
            perms.push('W');
        }
        if self.allow_upload {
            perms.push('U');
        }
        if self.is_admin {
            perms.push('A');
        }
        perms
    }
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct Preference {
    pub name: String,
    pub value: String,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct Draft {
    pub id: i64,
    pub pagepath: String,
    pub revision: String,
    pub author_email: String,
    pub content: String,
    pub cursor_line: i32,
    pub cursor_ch: i32,
    pub datetime: DateTime<Utc>,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct Cache {
    pub key: String,
    pub value: String,
    pub datetime: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Page {
    pub name: String,
    pub path: String,
    pub content: String,
    pub revision: String,
    pub author_name: String,
    pub author_email: String,
    pub datetime: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageHistory {
    pub revision: String,
    pub author_name: String,
    pub author_email: String,
    pub datetime: DateTime<Utc>,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangelogEntry {
    pub revision: String,
    pub author_name: String,
    pub author_email: String,
    pub datetime: DateTime<Utc>,
    pub message: String,
    pub files: Vec<String>,
}
