-- scripts/delete_accounts_request_and_dependents.sql
-- WARNING: destructive. Back up your DB before running.
-- This script discovers tables with foreign keys referencing `public.accounts_request`,
-- deletes rows from those tables first, then deletes rows from `public.accounts_request`.
-- It prints deletion counts using RAISE NOTICE messages.
-- Run this in Supabase SQL editor or via psql. Do NOT run on production without a backup.

DO $$
DECLARE
  target_schema TEXT := 'public';
  target_table TEXT := 'accounts_request';
  rec RECORD;
  deleted_count BIGINT;
  total_deleted BIGINT := 0;
  before_count BIGINT;
  after_count BIGINT;
BEGIN
  -- count before
  EXECUTE format('SELECT count(*) FROM %I.%I', target_schema, target_table) INTO before_count;
  RAISE NOTICE 'BEFORE: % rows in %.%', before_count, target_schema, target_table;

  -- find referencing FKs and delete from them first
  FOR rec IN
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.constraint_schema = kcu.constraint_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.constraint_schema = tc.constraint_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_schema = target_schema
      AND ccu.table_name = target_table
  LOOP
    -- delete dependent rows that reference the target table
    EXECUTE format('WITH d AS (DELETE FROM %I.%I WHERE %I IN (SELECT id FROM %I.%I) RETURNING 1) SELECT count(*) FROM d',
                   rec.table_schema, rec.table_name, rec.column_name, target_schema, target_table)
    INTO deleted_count;

    RAISE NOTICE 'Deleted % rows from %.%', deleted_count, rec.table_schema, rec.table_name;
    total_deleted := total_deleted + COALESCE(deleted_count,0);
  END LOOP;

  -- finally delete from the target table itself
  EXECUTE format('WITH d AS (DELETE FROM %I.%I RETURNING 1) SELECT count(*) FROM d', target_schema, target_table)
  INTO deleted_count;
  RAISE NOTICE 'Deleted % rows from %.%', deleted_count, target_schema, target_table;
  total_deleted := total_deleted + COALESCE(deleted_count,0);

  -- after count
  EXECUTE format('SELECT count(*) FROM %I.%I', target_schema, target_table) INTO after_count;
  RAISE NOTICE 'AFTER: % rows in %.%', after_count, target_schema, target_table;

  RAISE NOTICE 'Total deleted across all tables: %', total_deleted;
END$$;

-- Notes:
-- - If you prefer to TRUNCATE (faster, resets sequences) use: TRUNCATE TABLE public.accounts_request CASCADE;
-- - The script assumes the target table's primary key column is named `id`.
-- - If your primary key is different, edit the script accordingly.
-- - For very large tables, consider deleting in batches to avoid long-running transactions.
