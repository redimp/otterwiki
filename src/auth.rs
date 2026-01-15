use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use axum::{
    extract::State,
    response::{IntoResponse, Redirect, Response},
    Form,
};
use chrono::Utc;
use rand_core::OsRng;
use serde::Deserialize;

use crate::{error::AppError, models::User, state::AppState};

#[derive(Debug, Deserialize)]
pub struct LoginForm {
    pub email: String,
    pub password: String,
    pub remember: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct RegisterForm {
    pub name: String,
    pub email: String,
    pub password: String,
    pub password_confirm: String,
}

pub async fn login_form() -> impl IntoResponse {
    // Return login template
    "Login page"
}

pub async fn login(
    State(state): State<AppState>,
    Form(form): Form<LoginForm>,
) -> Result<Response, AppError> {
    let user = sqlx::query_as::<_, User>("SELECT * FROM user WHERE email = ?")
        .bind(&form.email)
        .fetch_optional(&state.db)
        .await?;
    
    if let Some(user) = user {
        if verify_password(&form.password, &user.password_hash)? {
            // Set session cookie
            // TODO: Implement session management
            return Ok(Redirect::to("/").into_response());
        }
    }
    
    Err(AppError::Auth("Invalid credentials".to_string()))
}

pub async fn logout() -> impl IntoResponse {
    Redirect::to("/")
}

pub async fn register_form(State(state): State<AppState>) -> Result<Response, AppError> {
    if state.config.disable_registration {
        return Err(AppError::Forbidden);
    }
    
    Ok("Register page".into_response())
}

pub async fn register(
    State(state): State<AppState>,
    Form(form): Form<RegisterForm>,
) -> Result<Response, AppError> {
    if state.config.disable_registration {
        return Err(AppError::Forbidden);
    }
    
    if form.password != form.password_confirm {
        return Err(AppError::Auth("Passwords do not match".to_string()));
    }
    
    let password_hash = hash_password(&form.password)?;
    
    let _result = sqlx::query(
        "INSERT INTO user (name, email, password_hash, first_seen, last_seen, is_approved, is_admin, email_confirmed, allow_read, allow_write, allow_upload) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    .bind(&form.name)
    .bind(&form.email)
    .bind(&password_hash)
    .bind(Utc::now())
    .bind(Utc::now())
    .bind(state.config.auto_approval)
    .bind(false)
    .bind(!state.config.email_needs_confirmation)
    .bind(false)
    .bind(false)
    .bind(false)
    .execute(&state.db)
    .await?;
    
    Ok(Redirect::to("/-/login").into_response())
}

fn hash_password(password: &str) -> Result<String, AppError> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let password_hash = argon2
        .hash_password(password.as_bytes(), &salt)
        .map_err(|e| AppError::Auth(format!("Password hashing failed: {}", e)))?
        .to_string();
    
    Ok(password_hash)
}

fn verify_password(password: &str, hash: &str) -> Result<bool, AppError> {
    let parsed_hash = PasswordHash::new(hash)
        .map_err(|e| AppError::Auth(format!("Invalid hash: {}", e)))?;
    
    Ok(Argon2::default()
        .verify_password(password.as_bytes(), &parsed_hash)
        .is_ok())
}
