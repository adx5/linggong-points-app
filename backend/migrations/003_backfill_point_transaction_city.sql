-- 003_backfill_point_transaction_city.sql
-- 目标：回填历史积分流水的 city_id。
-- 背景：修复前只有 scheduler 写入 city_id，结单/广告/兑换三条路径均为 NULL，按城市对账会失真。
-- 策略：先把「自身没有城市」的历史账号补成默认城市，再按用户当前城市回填流水。
-- 全部语句幂等（只处理 NULL 行），可重复执行。

-- 1. 历史账号补默认城市（默认城市取自 global_configs，不硬编码）
UPDATE users
SET city_id = (SELECT value FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
WHERE city_id IS NULL
  AND EXISTS (SELECT 1 FROM global_configs WHERE key = 'DEFAULT_CITY_ID');

UPDATE cooperation_entities
SET city_id = (SELECT value FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
WHERE city_id IS NULL
  AND EXISTS (SELECT 1 FROM global_configs WHERE key = 'DEFAULT_CITY_ID');

-- 2. 回填积分流水
UPDATE point_transactions pt
SET city_id = u.city_id
FROM users u
WHERE pt.user_id = u.id
  AND pt.city_id IS NULL
  AND u.city_id IS NOT NULL;

-- 3. 回填历史岗位的 city_id（修复前发布的岗位 city_id 为空 → C 端列表永远查不到）
--    按发布商家所属城市精确回填，不使用默认城市兜底
UPDATE jobs j
SET city_id = u.city_id
FROM users u
WHERE j.merchant_id = u.id
  AND j.city_id IS NULL
  AND u.city_id IS NOT NULL;
