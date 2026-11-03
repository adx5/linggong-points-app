-- backend/migrations/001_add_city_id_down.sql (数据库回滚脚本：城市隔离改造)
-- ⚠️ 注意：此脚本仅供降级测试，线上执行前必须冷备。
DROP INDEX IF EXISTS ix_users_city_id;
DROP INDEX IF EXISTS ix_jobs_city_id;
DROP INDEX IF EXISTS ix_applications_city_id;

ALTER TABLE users DROP COLUMN IF EXISTS city_id;
ALTER TABLE users DROP COLUMN IF EXISTS role;
ALTER TABLE users DROP COLUMN IF EXISTS token_version;
ALTER TABLE users DROP COLUMN IF EXISTS available_roles;
ALTER TABLE cooperation_entities DROP COLUMN IF EXISTS city_id;
ALTER TABLE entity_certificates DROP COLUMN IF EXISTS city_id;
ALTER TABLE jobs DROP COLUMN IF EXISTS city_id;
ALTER TABLE job_applications DROP COLUMN IF EXISTS city_id;
ALTER TABLE job_applications DROP COLUMN IF EXISTS business_city_id;
ALTER TABLE application_logs DROP COLUMN IF EXISTS city_id;
ALTER TABLE interviews DROP COLUMN IF EXISTS city_id;
ALTER TABLE reviews DROP COLUMN IF EXISTS city_id;
ALTER TABLE notifications DROP COLUMN IF EXISTS city_id;
ALTER TABLE audit_logs DROP COLUMN IF EXISTS city_id;
ALTER TABLE point_transactions DROP COLUMN IF EXISTS city_id;
ALTER TABLE service_orders DROP COLUMN IF EXISTS city_id;
ALTER TABLE reports DROP COLUMN IF EXISTS city_id;
ALTER TABLE blacklists DROP COLUMN IF EXISTS city_id;
ALTER TABLE exchange_orders DROP COLUMN IF EXISTS city_id;
ALTER TABLE verification_codes DROP COLUMN IF EXISTS city_id;
ALTER TABLE withdrawals DROP COLUMN IF EXISTS city_id;
ALTER TABLE profit_sharing_bills DROP COLUMN IF EXISTS city_id;
ALTER TABLE temp_authorizations DROP COLUMN IF EXISTS city_id;
ALTER TABLE export_logs DROP COLUMN IF EXISTS city_id;
ALTER TABLE high_risk_approvals DROP COLUMN IF EXISTS city_id;

DROP TABLE IF EXISTS cities;