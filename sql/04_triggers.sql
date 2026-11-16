-- Trigger function: auto-add owner as 'owner' collaborator on repo creation
CREATE OR REPLACE FUNCTION add_owner_as_collaborator()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO collaborators (repo_id, user_id, role)
    VALUES (NEW.id, NEW.owner_id, 'owner')
    ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_add_owner_collaborator ON repositories;
CREATE TRIGGER trg_add_owner_collaborator
AFTER INSERT ON repositories
FOR EACH ROW EXECUTE FUNCTION add_owner_as_collaborator();
