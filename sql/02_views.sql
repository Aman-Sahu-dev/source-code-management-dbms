-- repo_summary view: repo info + owner username + commit count + open issue count
CREATE OR REPLACE VIEW repo_summary AS
SELECT
    r.id,
    r.name,
    r.description,
    r.is_private,
    r.created_at,
    u.username AS owner_username,
    u.id AS owner_id,
    COUNT(DISTINCT c.id) AS commit_count,
    COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'open') AS open_issue_count
FROM repositories r
JOIN users u ON r.owner_id = u.id
LEFT JOIN branches b ON b.repo_id = r.id
LEFT JOIN commits c ON c.branch_id = b.id
LEFT JOIN issues i ON i.repo_id = r.id
GROUP BY r.id, u.id;
