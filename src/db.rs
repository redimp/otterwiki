use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use crate::config::Config;

pub async fn init_db(config: &Config) -> anyhow::Result<SqlitePool> {
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&config.database_url)
        .await?;
    
    // Run migrations
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await?;
    
    Ok(pool)
}
