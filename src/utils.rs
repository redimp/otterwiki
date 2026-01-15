pub fn sanitize_pagename(name: &str, retain_case: bool) -> String {
    let mut result = name
        .replace(" ", "_")
        .chars()
        .filter(|c| c.is_alphanumeric() || *c == '_' || *c == '-' || *c == '/')
        .collect::<String>();
    
    if !retain_case {
        result = result.to_lowercase();
    }
    
    result
}

pub fn format_datetime(dt: &chrono::DateTime<chrono::Utc>, format: &str) -> String {
    match format {
        "medium" => dt.format("%Y-%m-%d %H:%M").to_string(),
        "full" => dt.format("%Y-%m-%d %H:%M:%S").to_string(),
        _ => dt.to_rfc3339(),
    }
}

pub fn sizeof_fmt(num: u64) -> String {
    const UNITS: [&str; 7] = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"];
    
    if num < 1024 {
        return format!("{} B", num);
    }
    
    let mut size = num as f64;
    let mut unit_index = 0;
    
    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }
    
    format!("{:.1} {}", size, UNITS[unit_index])
}
