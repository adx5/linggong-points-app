-- 002_add_unique_job_worker_down.sql
-- 回滚：移除防重复投递唯一约束

ALTER TABLE job_applications DROP CONSTRAINT IF EXISTS uq_job_worker;
