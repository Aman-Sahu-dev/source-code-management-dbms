CREATE INDEX IF NOT EXISTS idx_commits_branch_id ON commits(branch_id);
CREATE INDEX IF NOT EXISTS idx_issues_repo_id ON issues(repo_id);
CREATE INDEX IF NOT EXISTS idx_repositories_owner_id ON repositories(owner_id);
CREATE INDEX IF NOT EXISTS idx_branches_repo_id ON branches(repo_id);
CREATE INDEX IF NOT EXISTS idx_collaborators_user_id ON collaborators(user_id);
