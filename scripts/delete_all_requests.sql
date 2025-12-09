-- scripts/delete_all_requests.sql
-- WARNING: destructive. Back up your DB before running.
-- This script inspects constraints, shows counts, and deletes all rows from public.request
-- Run from psql, Supabase SQL editor, or Supabase CLI.

-- 1) Show how many rows exist now
SELECT 'BEFORE' AS phase, count(*) AS request_count FROM public.request;

-- 2) Show any foreign keys referencing this table (helpful to inspect before deletion)
SELECT
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM
  information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY'
  AND (tc.table_name = 'request' OR ccu.table_name = 'request');

-- 3) Preview first 20 ids (optional)
SELECT id FROM public.request ORDER BY id LIMIT 20;

-- 4) Delete all rows in a transaction and return number deleted
BEGIN;
WITH deleted AS (
  DELETE FROM public.request
  RETURNING id
)
SELECT count(*) AS deleted_count FROM deleted;
COMMIT;

-- 5) Confirm zero rows remain
SELECT 'AFTER' AS phase, count(*) AS request_count FROM public.request;

-- If you need to delete dependent tables first because of foreign-keys without ON DELETE CASCADE,
-- uncomment and adapt the following block (replace dependent_table and request_id):
-- BEGIN;
-- DELETE FROM dependent_table WHERE request_id IN (SELECT id FROM public.request);
-- DELETE FROM public.request;
-- COMMIT;

-- End of script
