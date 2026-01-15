use anyhow::{anyhow, Result};
use chrono::{TimeZone, Utc};
use git2::{Commit, ObjectType, Oid, Repository, Signature};
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use crate::models::{ChangelogEntry, PageHistory};

pub struct GitStorage {
    repo: Mutex<Repository>,
    path: PathBuf,
}

impl GitStorage {
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        
        let repo = if path.join(".git").exists() {
            Repository::open(&path)?
        } else {
            Repository::init(&path)?
        };
        
        Ok(Self { 
            repo: Mutex::new(repo),
            path 
        })
    }
    
    pub fn exists(&self, filename: &str) -> bool {
        self.path.join(filename).exists()
    }
    
    pub fn load(&self, filename: &str, revision: Option<&str>) -> Result<String> {
        if let Some(rev) = revision {
            self.load_from_revision(filename, rev)
        } else {
            self.load_from_filesystem(filename)
        }
    }
    
    fn load_from_filesystem(&self, filename: &str) -> Result<String> {
        let file_path = self.path.join(filename);
        std::fs::read_to_string(&file_path)
            .map_err(|_| anyhow!("File not found: {}", filename))
    }
    
    fn load_from_revision(&self, filename: &str, revision: &str) -> Result<String> {
        let repo = self.repo.lock().unwrap();
        let oid = Oid::from_str(revision)?;
        let commit = repo.find_commit(oid)?;
        let tree = commit.tree()?;
        let entry = tree.get_path(Path::new(filename))?;
        let object = entry.to_object(&repo)?;
        
        if object.kind() != Some(ObjectType::Blob) {
            return Err(anyhow!("Not a file: {}", filename));
        }
        
        let blob = object.as_blob().ok_or(anyhow!("Invalid blob"))?;
        let content = std::str::from_utf8(blob.content())?;
        
        Ok(content.to_string())
    }
    
    pub fn store(
        &self,
        filename: &str,
        content: &str,
        author_name: &str,
        author_email: &str,
        message: &str,
    ) -> Result<String> {
        // Write to filesystem
        let file_path = self.path.join(filename);
        
        if let Some(parent) = file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        
        std::fs::write(&file_path, content)?;
        
        // Git operations
        let repo = self.repo.lock().unwrap();
        let mut index = repo.index()?;
        index.add_path(Path::new(filename))?;
        index.write()?;
        
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        
        let signature = Signature::now(author_name, author_email)?;
        
        let parent_commit = repo.head().ok().and_then(|h| h.peel_to_commit().ok());
        let parents = if let Some(ref commit) = parent_commit {
            vec![commit]
        } else {
            vec![]
        };
        
        let oid = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parents,
        )?;
        
        Ok(oid.to_string())
    }
    
    pub fn delete(
        &self,
        filename: &str,
        author_name: &str,
        author_email: &str,
        message: &str,
    ) -> Result<String> {
        let file_path = self.path.join(filename);
        
        if file_path.exists() {
            std::fs::remove_file(&file_path)?;
        }
        
        let repo = self.repo.lock().unwrap();
        let mut index = repo.index()?;
        index.remove_path(Path::new(filename))?;
        index.write()?;
        
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        
        let signature = Signature::now(author_name, author_email)?;
        
        let parent_commit = repo.head().ok().and_then(|h| h.peel_to_commit().ok());
        let parents = if let Some(ref commit) = parent_commit {
            vec![commit]
        } else {
            vec![]
        };
        
        let oid = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parents,
        )?;
        
        Ok(oid.to_string())
    }
    
    pub fn list_pages(&self) -> Result<Vec<String>> {
        let repo = self.repo.lock().unwrap();
        let head = repo.head()?;
        let tree = head.peel_to_tree()?;
        
        let mut pages = Vec::new();
        self.collect_md_files(&tree, "", &mut pages)?;
        
        Ok(pages)
    }
    
    fn collect_md_files(&self, tree: &git2::Tree, prefix: &str, pages: &mut Vec<String>) -> Result<()> {
        let repo = self.repo.lock().unwrap();
        for entry in tree.iter() {
            let name = entry.name().unwrap_or("");
            let path = if prefix.is_empty() {
                name.to_string()
            } else {
                format!("{}/{}", prefix, name)
            };
            
            if let Some(obj) = entry.to_object(&repo).ok() {
                match obj.kind() {
                    Some(ObjectType::Tree) => {
                        if let Some(subtree) = obj.as_tree() {
                            self.collect_md_files(subtree, &path, pages)?;
                        }
                    }
                    Some(ObjectType::Blob) => {
                        if name.ends_with(".md") {
                            pages.push(path);
                        }
                    }
                    _ => {}
                }
            }
        }
        
        Ok(())
    }
    
    pub fn get_page_history(&self, filename: &str, limit: usize) -> Result<Vec<PageHistory>> {
        let repo = self.repo.lock().unwrap();
        let mut revwalk = repo.revwalk()?;
        revwalk.push_head()?;
        
        let mut history = Vec::new();
        
        for oid in revwalk {
            let oid = oid?;
            let commit = repo.find_commit(oid)?;
            
            if self.commit_affects_file(&commit, filename)? {
                history.push(PageHistory {
                    revision: oid.to_string(),
                    author_name: commit.author().name().unwrap_or("Unknown").to_string(),
                    author_email: commit.author().email().unwrap_or("").to_string(),
                    datetime: Utc.timestamp_opt(commit.time().seconds(), 0).unwrap(),
                    message: commit.message().unwrap_or("").to_string(),
                });
                
                if history.len() >= limit {
                    break;
                }
            }
        }
        
        Ok(history)
    }
    
    pub fn get_changelog(&self, limit: usize) -> Result<Vec<ChangelogEntry>> {
        let repo = self.repo.lock().unwrap();
        let mut revwalk = repo.revwalk()?;
        revwalk.push_head()?;
        
        let mut changelog = Vec::new();
        
        for oid in revwalk.take(limit) {
            let oid = oid?;
            let commit = repo.find_commit(oid)?;
            
            changelog.push(ChangelogEntry {
                revision: oid.to_string(),
                author_name: commit.author().name().unwrap_or("Unknown").to_string(),
                author_email: commit.author().email().unwrap_or("").to_string(),
                datetime: Utc.timestamp_opt(commit.time().seconds(), 0).unwrap(),
                message: commit.message().unwrap_or("").to_string(),
                files: self.get_commit_files(&commit)?,
            });
        }
        
        Ok(changelog)
    }
    
    fn commit_affects_file(&self, commit: &Commit, filename: &str) -> Result<bool> {
        let tree = commit.tree()?;
        Ok(tree.get_path(Path::new(filename)).is_ok())
    }
    
    fn get_commit_files(&self, commit: &Commit) -> Result<Vec<String>> {
        let tree = commit.tree()?;
        let mut files = Vec::new();
        
        self.collect_all_files(&tree, "", &mut files)?;
        
        Ok(files)
    }
    
    fn collect_all_files(&self, tree: &git2::Tree, prefix: &str, files: &mut Vec<String>) -> Result<()> {
        let repo = self.repo.lock().unwrap();
        for entry in tree.iter() {
            let name = entry.name().unwrap_or("");
            let path = if prefix.is_empty() {
                name.to_string()
            } else {
                format!("{}/{}", prefix, name)
            };
            
            if let Some(obj) = entry.to_object(&repo).ok() {
                match obj.kind() {
                    Some(ObjectType::Tree) => {
                        if let Some(subtree) = obj.as_tree() {
                            self.collect_all_files(subtree, &path, files)?;
                        }
                    }
                    Some(ObjectType::Blob) => {
                        files.push(path);
                    }
                    _ => {}
                }
            }
        }
        
        Ok(())
    }
}
