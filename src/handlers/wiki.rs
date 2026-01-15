use axum::{
    extract::{Path, Query, State},
    response::{Html, IntoResponse, Redirect, Response},
    Form,
};
use serde::Deserialize;

use crate::{error::AppError, markdown::MarkdownRenderer, state::AppState, utils::sanitize_pagename};

#[derive(Deserialize)]
pub struct SearchQuery {
    q: Option<String>,
}

#[derive(Deserialize)]
pub struct PageForm {
    content: String,
    message: Option<String>,
}

pub async fn index() -> impl IntoResponse {
    Redirect::to("/home")
}

pub async fn view_page(
    State(state): State<AppState>,
    Path(page): Path<String>,
) -> Result<Response, AppError> {
    let pagename = sanitize_pagename(&page, state.config.retain_page_name_case);
    let filename = format!("{}.md", pagename);
    
    let content = state.storage.load(&filename, None)
        .map_err(|_| AppError::NotFound(format!("Page {} not found", page)))?;
    
    let renderer = MarkdownRenderer::new();
    let html = renderer.render(&content);
    
    Ok(Html(format!(
        r#"<!DOCTYPE html>
        <html>
        <head><title>{} - {}</title></head>
        <body>
        <h1>{}</h1>
        <div>{}</div>
        <a href="/{}/edit">Edit</a>
        </body>
        </html>"#,
        page, state.config.site_name, page, html, page
    )).into_response())
}

pub async fn edit_page(
    State(state): State<AppState>,
    Path(page): Path<String>,
) -> Result<Response, AppError> {
    let pagename = sanitize_pagename(&page, state.config.retain_page_name_case);
    let filename = format!("{}.md", pagename);
    
    let content = state.storage.load(&filename, None).unwrap_or_default();
    
    Ok(Html(format!(
        r#"<!DOCTYPE html>
        <html>
        <head><title>Edit {} - {}</title></head>
        <body>
        <h1>Edit {}</h1>
        <form method="post">
        <textarea name="content" rows="20" cols="80">{}</textarea><br>
        <input type="text" name="message" placeholder="Commit message"><br>
        <button type="submit">Save</button>
        </form>
        </body>
        </html>"#,
        page, state.config.site_name, page, content
    )).into_response())
}

pub async fn save_page(
    State(state): State<AppState>,
    Path(page): Path<String>,
    Form(form): Form<PageForm>,
) -> Result<Response, AppError> {
    let pagename = sanitize_pagename(&page, state.config.retain_page_name_case);
    let filename = format!("{}.md", pagename);
    
    let message = form.message.unwrap_or_else(|| format!("Updated {}", page));
    
    state.storage.store(
        &filename,
        &form.content,
        "Anonymous", // TODO: Get from session
        "",
        &message,
    )?;
    
    Ok(Redirect::to(&format!("/{}", page)).into_response())
}

pub async fn page_history(
    State(state): State<AppState>,
    Path(page): Path<String>,
) -> Result<Response, AppError> {
    let pagename = sanitize_pagename(&page, state.config.retain_page_name_case);
    let filename = format!("{}.md", pagename);
    
    let history = state.storage.get_page_history(&filename, 100)?;
    
    let mut html = format!("<h1>History of {}</h1><ul>", page);
    for entry in history {
        html.push_str(&format!(
            "<li>{} - {} by {} ({})</li>",
            entry.datetime.format("%Y-%m-%d %H:%M"),
            entry.message,
            entry.author_name,
            entry.revision
        ));
    }
    html.push_str("</ul>");
    
    Ok(Html(html).into_response())
}

pub async fn page_index(State(state): State<AppState>) -> Result<Response, AppError> {
    let pages = state.storage.list_pages()?;
    
    let mut html = String::from("<h1>Page Index</h1><ul>");
    for page in pages {
        let name = page.trim_end_matches(".md");
        html.push_str(&format!("<li><a href=\"/{}\">{}</a></li>", name, name));
    }
    html.push_str("</ul>");
    
    Ok(Html(html).into_response())
}

pub async fn changelog(State(state): State<AppState>) -> Result<Response, AppError> {
    let entries = state.storage.get_changelog(100)?;
    
    let mut html = String::from("<h1>Changelog</h1><ul>");
    for entry in entries {
        html.push_str(&format!(
            "<li>{} - {} by {}</li>",
            entry.datetime.format("%Y-%m-%d %H:%M"),
            entry.message,
            entry.author_name
        ));
    }
    html.push_str("</ul>");
    
    Ok(Html(html).into_response())
}

pub async fn search(
    State(state): State<AppState>,
    Query(query): Query<SearchQuery>,
) -> impl IntoResponse {
    Html("<h1>Search</h1><p>Search functionality not yet implemented</p>")
}

pub async fn create_page() -> impl IntoResponse {
    Html("<h1>Create Page</h1><p>Create page functionality not yet implemented</p>")
}

pub async fn attachments(
    State(state): State<AppState>,
    Path(page): Path<String>,
) -> impl IntoResponse {
    Html("<h1>Attachments</h1><p>Attachments not yet implemented</p>")
}

pub async fn about(State(state): State<AppState>) -> impl IntoResponse {
    Html(format!(
        r#"<h1>About {}</h1>
        <p>An Otter Wiki - Rust Edition</p>
        <p>Version: {}</p>"#,
        state.config.site_name,
        env!("CARGO_PKG_VERSION")
    ))
}

pub async fn help() -> impl IntoResponse {
    Html("<h1>Help</h1><p>Help content here</p>")
}

pub async fn help_topic(Path(topic): Path<String>) -> impl IntoResponse {
    Html(format!("<h1>Help: {}</h1><p>Help content for {} here</p>", topic, topic))
}

pub async fn syntax() -> impl IntoResponse {
    Html("<h1>Markdown Syntax</h1><p>Syntax guide here</p>")
}
