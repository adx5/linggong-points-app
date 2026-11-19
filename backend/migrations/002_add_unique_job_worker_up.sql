-- 002_add_unique_job_worker_up.sql
-- 目标：防重复投递。
-- 原实现仅靠应用层 SELECT 查重（并尝试捕获一个永远不会触发的 duplicate key），
-- 并发请求下仍会产生同一工人对同一岗位的多条投递记录。

-- 1. 清理历史重复数据 ------------------------------------------------------
--    规则：每个 (job_id, worker_id) 只保留 id 最小的一条。
--    必须先删引用 application.id 的子表数据，否则外键会阻止删除。

DELETE FROM application_logs
WHERE application_id IN (
    SELECT a.id
    FROM job_applications a
    JOIN job_applications b
      ON a.job_id = b.job_id
     AND a.worker_id = b.worker_id
     AND a.id > b.id
);

DELETE FROM reviews
WHERE application_id IN (
    SELECT a.id
    FROM job_applications a
    JOIN job_applications b
      ON a.job_id = b.job_id
     AND a.worker_id = b.worker_id
     AND a.id > b.id
);

DELETE FROM job_applications a
USING job_applications b
WHERE a.job_id = b.job_id
  AND a.worker_id = b.worker_id
  AND a.id > b.id;

-- 2. 加唯一约束（幂等，可重复执行）----------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_job_worker'
    ) THEN
        ALTER TABLE job_applications
            ADD CONSTRAINT uq_job_worker UNIQUE (job_id, worker_id);
    END IF;
END $$;
