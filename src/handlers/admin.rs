use axum::{
    extract::State,
    response::{IntoResponse, Response},
};

use crate::state::AppState;

pub async fn admin_panel(State(state): State<AppState>) -> impl IntoResponse {
    "Admin panel"
}

pub async fn handle_admin(State(state): State<AppState>) -> impl IntoResponse {
    "Handle admin"
}

pub async fn user_management(State(state): State<AppState>) -> impl IntoResponse {
    "User management"
}

pub async fn handle_user_management(State(state): State<AppState>) -> impl IntoResponse {
    "Handle user management"
}
