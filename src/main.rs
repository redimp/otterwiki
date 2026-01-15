mod auth;
mod config;
mod db;
mod error;
mod git_storage;
mod handlers;
mod markdown;
mod models;
mod state;
mod templates;
mod utils;

use axum::{
    routing::get,
    Router,
};
use std::net::SocketAddr;
use tower_http::{
    compression::CompressionLayer,
    services::ServeDir,
    trace::TraceLayer,
};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::config::Config;
use crate::state::AppState;

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "otterwiki=info,tower_http=debug,axum=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("*** Starting An Otter Wiki (Rust) {}", VERSION);

    // Load configuration
    let config = Config::load()?;
    
    // Initialize database
    let db_pool = db::init_db(&config).await?;
    
    // Initialize git storage
    let git_storage = git_storage::GitStorage::new(&config.repository)?;
    
    // Create application state
    let state = AppState::new(config.clone(), db_pool, git_storage).await?;

    // Build the router
    let app = Router::new()
        // Main routes
        .route("/", get(handlers::wiki::index))
        .route("/robots.txt", get(handlers::static_files::robots_txt))
        .route("/sitemap.xml", get(handlers::static_files::sitemap))
        .route("/favicon.ico", get(handlers::static_files::favicon))
        .route("/-/healthz", get(handlers::static_files::healthz))
        
        // Wiki routes
        .route("/-/about", get(handlers::wiki::about))
        .route("/-/help", get(handlers::wiki::help))
        .route("/-/help/:topic", get(handlers::wiki::help_topic))
        .route("/-/syntax", get(handlers::wiki::syntax))
        
        // Page operations
        .route("/-/pageindex", get(handlers::wiki::page_index))
        .route("/-/changelog", get(handlers::wiki::changelog))
        .route("/-/search", get(handlers::wiki::search))
        .route("/-/createpage", get(handlers::wiki::create_page))
        
        // Auth routes
        .route("/-/login", get(handlers::auth::login_form).post(handlers::auth::login))
        .route("/-/logout", get(handlers::auth::logout))
        .route("/-/register", get(handlers::auth::register_form).post(handlers::auth::register))
        
        // Admin routes
        .route("/-/admin", get(handlers::admin::admin_panel).post(handlers::admin::handle_admin))
        .route("/-/admin/user_management", get(handlers::admin::user_management).post(handlers::admin::handle_user_management))
        
        // Page view/edit
        .route("/:page", get(handlers::wiki::view_page))
        .route("/:page/edit", get(handlers::wiki::edit_page).post(handlers::wiki::save_page))
        .route("/:page/history", get(handlers::wiki::page_history))
        .route("/:page/attachments", get(handlers::wiki::attachments))
        
        // Serve static files
        .nest_service("/static", ServeDir::new("static"))
        
        // Middleware
        .layer(CompressionLayer::new())
        .layer(TraceLayer::new_for_http())
        
        // State
        .with_state(state);

    // Start server
    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    tracing::info!("Listening on http://{}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
