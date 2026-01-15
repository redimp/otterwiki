use axum::{
    response::IntoResponse,
};

pub async fn admin_panel() -> impl IntoResponse {
    "Admin panel"
}

pub async fn handle_admin() -> impl IntoResponse {
    "Handle admin"
}

pub async fn user_management() -> impl IntoResponse {
    "User management"
}

pub async fn handle_user_management() -> impl IntoResponse {
    "Handle user management"
}
