use axum::{
    body::Body,
    extract::State,
    http::{header, StatusCode},
    response::{IntoResponse, Response},
};

use crate::state::AppState;

pub async fn robots_txt(State(state): State<AppState>) -> impl IntoResponse {
    let content = if state.config.robots_txt == "allow" {
        "User-agent: *\nAllow: /"
    } else {
        "User-agent: *\nDisallow: /"
    };
    
    Response::builder()
        .status(StatusCode::OK)
        .header(header::CONTENT_TYPE, "text/plain")
        .body(Body::from(content))
        .unwrap()
}

pub async fn sitemap() -> impl IntoResponse {
    Response::builder()
        .status(StatusCode::OK)
        .header(header::CONTENT_TYPE, "application/xml")
        .body(Body::from(
            r#"<?xml version="1.0" encoding="UTF-8"?>
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            </urlset>"#
        ))
        .unwrap()
}

pub async fn favicon() -> impl IntoResponse {
    // Return empty response - should serve actual favicon
    StatusCode::NOT_FOUND
}

pub async fn healthz(State(state): State<AppState>) -> impl IntoResponse {
    // Basic health check
    let healthy = state.storage.list_pages().is_ok();
    
    if healthy {
        (StatusCode::OK, "OK")
    } else {
        (StatusCode::SERVICE_UNAVAILABLE, "UNHEALTHY")
    }
}
