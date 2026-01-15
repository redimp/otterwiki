use crate::{config::Config, git_storage::GitStorage};
use sqlx::SqlitePool;
use std::sync::Arc;

#[derive(Clone)]
pub struct AppState {
    pub config: Arc<Config>,
    pub db: SqlitePool,
    pub storage: Arc<GitStorage>,
}

impl AppState {
    pub async fn new(
        config: Config,
        db: SqlitePool,
        storage: GitStorage,
    ) -> anyhow::Result<Self> {
        // Initialize home page if repository is empty
        let pages = storage.list_pages()?;
        if pages.is_empty() {
            let initial_content = include_str!("../otterwiki/initial_home.md");
            let filename = if config.retain_page_name_case {
                "Home.md"
            } else {
                "home.md"
            };
            
            storage.store(
                filename,
                initial_content,
                "Otterwiki Robot",
                "noreply@otterwiki",
                "Initial commit",
            )?;
            
            tracing::info!("Created initial /Home page");
        }
        
        Ok(Self {
            config: Arc::new(config),
            db,
            storage: Arc::new(storage),
        })
    }
}
