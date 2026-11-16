-- Function: returns commit count and issue count for a repo
CREATE OR REPLACE FUNCTION get_repo_stats(p_repo_id INTEGER)
RETURNS TABLE(commit_count BIGINT, issue_count BIGINT, open_issue_count BIGINT)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT c.id)::BIGINT AS commit_count,
        COUNT(DISTINCT i.id)::BIGINT AS issue_count,
        COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'open')::BIGINT AS open_issue_count
    FROM repositories r
    LEFT JOIN branches b ON b.repo_id = r.id
    LEFT JOIN commits c ON c.branch_id = b.id
    LEFT JOIN issues i ON i.repo_id = r.id
    WHERE r.id = p_repo_id;
END;
$$;

-- Procedure: close an issue
CREATE OR REPLACE PROCEDURE close_issue(p_issue_id INTEGER)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE issues SET status = 'closed' WHERE id = p_issue_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Issue % not found', p_issue_id;
    END IF;
END;
$$;
