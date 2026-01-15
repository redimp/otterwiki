use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(default = "default_port")]
    pub port: u16,
    
    #[serde(default = "default_debug")]
    pub debug: bool,
    
    pub repository: PathBuf,
    pub secret_key: String,
    
    #[serde(default = "default_site_name")]
    pub site_name: String,
    
    pub site_description: Option<String>,
    pub site_logo: Option<String>,
    pub site_icon: Option<String>,
    
    #[serde(default = "default_site_lang")]
    pub site_lang: String,
    
    #[serde(default)]
    pub hide_logo: bool,
    
    #[serde(default = "default_read_access")]
    pub read_access: AccessLevel,
    
    #[serde(default = "default_write_access")]
    pub write_access: AccessLevel,
    
    #[serde(default = "default_attachment_access")]
    pub attachment_access: AccessLevel,
    
    #[serde(default = "default_auto_approval")]
    pub auto_approval: bool,
    
    #[serde(default)]
    pub disable_registration: bool,
    
    #[serde(default = "default_email_needs_confirmation")]
    pub email_needs_confirmation: bool,
    
    #[serde(default)]
    pub retain_page_name_case: bool,
    
    #[serde(default = "default_database_url")]
    pub database_url: String,
    
    #[serde(default)]
    pub mail_config: MailConfig,
    
    #[serde(default = "default_commit_message")]
    pub commit_message: CommitMessageMode,
    
    #[serde(default)]
    pub git_web_server: bool,
    
    #[serde(default = "default_robots_txt")]
    pub robots_txt: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "UPPERCASE")]
pub enum AccessLevel {
    Anonymous,
    Registered,
    Approved,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "UPPERCASE")]
pub enum CommitMessageMode {
    Required,
    Optional,
    Disabled,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MailConfig {
    pub server: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub use_tls: bool,
    pub use_ssl: bool,
    pub default_sender: String,
}

impl Config {
    pub fn load() -> anyhow::Result<Self> {
        dotenv::dotenv().ok();
        
        let mut config = config::Config::builder();
        
        // Load from file if exists
        if std::path::Path::new("settings.toml").exists() {
            config = config.add_source(config::File::with_name("settings"));
        }
        
        // Override with environment variables
        config = config.add_source(
            config::Environment::with_prefix("OTTERWIKI")
                .separator("_")
        );
        
        let config = config.build()?;
        let app_config: Config = config.try_deserialize()?;
        
        // Validate configuration
        app_config.validate()?;
        
        Ok(app_config)
    }
    
    fn validate(&self) -> anyhow::Result<()> {
        if self.secret_key.len() < 16 || self.secret_key == "CHANGE ME" {
            anyhow::bail!("Please configure a random SECRET_KEY with at least 16 characters");
        }
        
        if !self.repository.exists() {
            anyhow::bail!("Repository path {:?} not found", self.repository);
        }
        
        Ok(())
    }
}

fn default_port() -> u16 {
    8080
}

fn default_debug() -> bool {
    false
}

fn default_site_name() -> String {
    "An Otter Wiki".to_string()
}

fn default_site_lang() -> String {
    "en".to_string()
}

fn default_read_access() -> AccessLevel {
    AccessLevel::Anonymous
}

fn default_write_access() -> AccessLevel {
    AccessLevel::Anonymous
}

fn default_attachment_access() -> AccessLevel {
    AccessLevel::Anonymous
}

fn default_auto_approval() -> bool {
    true
}

fn default_email_needs_confirmation() -> bool {
    true
}

fn default_database_url() -> String {
    "sqlite://otterwiki.db".to_string()
}

fn default_commit_message() -> CommitMessageMode {
    CommitMessageMode::Required
}

fn default_robots_txt() -> String {
    "allow".to_string()
}
