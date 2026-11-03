-- backend/migrations/001_add_city_id_up.sql (数据库迁移脚本：城市隔离改造与角色池初始化)
-- 1. 创建城市字典
CREATE TABLE IF NOT EXISTS cities (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);
INSERT INTO cities (id, name) VALUES ('410185', '登封'), ('410173', '航空港'), ('411300', '南阳') ON CONFLICT DO NOTHING;

-- 2. 添加用户字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INT DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'worker' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS available_roles VARCHAR(100) DEFAULT 'worker';
-- 将老数据的角色池回填为当前的 role
UPDATE users SET available_roles = role WHERE available_roles = 'worker' OR available_roles IS NULL;

-- 3. 为 21 张表添加 city_id
ALTER TABLE users ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE cooperation_entities ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE entity_certificates ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS business_city_id VARCHAR(10);
ALTER TABLE application_logs ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE interviews ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE point_transactions ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE service_orders ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE blacklists ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE exchange_orders ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE verification_codes ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE withdrawals ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE profit_sharing_bills ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE temp_authorizations ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE export_logs ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);
ALTER TABLE high_risk_approvals ADD COLUMN IF NOT EXISTS city_id VARCHAR(10);

-- 4. 建议手动为高频查询字段建立索引 (示例)
CREATE INDEX IF NOT EXISTS ix_users_city_id ON users(city_id);
CREATE INDEX IF NOT EXISTS ix_jobs_city_id ON jobs(city_id);
CREATE INDEX IF NOT EXISTS ix_applications_city_id ON job_applications(city_id);