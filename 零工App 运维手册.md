📖 linggong-V2 项目运维与开发手册
一、 全局架构与规范
本项目采用 前后端分离 架构，并严格实行 多端物理隔离。

前端：Vue3 + Vite + Pinia（H5 移动端）。

后端：FastAPI + PostgreSQL (Neon) + SQLAlchemy。

路径红线：本地终端启动时，后端必须在 backend 目录，前端必须在 frontend 目录。代码中所有的互相导入（import）严禁带 backend. 前缀。

二、 核心环境变量配置 (backend/.env)
在 backend 根目录下必须有 .env 文件（千万别传 GitHub）：

env
# 1. 数据库连接串（必须使用直连，不要用 -pooler 连接池）
DATABASE_URL=postgresql://neondb_owner:你的密码@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# 2. JWT 鉴权密钥（随便写一串复杂的，一旦设置不要乱改）
SECRET_KEY=linggong_v2_secret_2026_abcdefg

# 3. Redis 连接串（本地没装 Redis 也没关系，代码内已做降级处理）
REDIS_URL=redis://localhost:6379/0
三、 本地开发启动 SOP
💻 后端启动 (FastAPI)
powershell
cd E:\Code\linggong-V2\backend
# 激活虚拟环境
.\.venv\Scripts\activate
# 安装依赖（第一次或依赖更新时）
pip install -r requirements.txt
# 启动服务（端口 8888）
uvicorn main:app --reload --port 8888
访问 Swagger 接口文档：http://127.0.0.1:8888/docs

📱 前端启动 (Vue3)
新开一个终端窗口：

powershell
cd E:\Code\linggong-V2\frontend
# 安装依赖（第一次）
npm install
# 启动服务（端口 5173）
npm run dev
访问 H5 页面：http://localhost:5173

四、 数据库运维 (Neon PostgreSQL)
1. 表结构更新问题（极度重要）
如果代码 models.py 中加了新字段，但数据库里没加，FastAPI 查询会直接报 500（如 column users.xxx does not exist）。

最快解决办法：直接在 Neon 控制台的 SQL Editor 中执行 DROP SCHEMA public CASCADE; CREATE SCHEMA public;。然后重启后端，让 FastAPI 自动建全新表。

2. 快速清理测试数据
保留表结构，只想清空脏数据：

sql
TRUNCATE TABLE users, jobs, job_applications, ad_callback_log RESTART IDENTITY CASCADE;
五、 常见故障排查 SOP (Troubleshooting)
报错现象	根本原因	解决方案
登录报 500 / 查表报 UndefinedColumn	数据库表结构未同步	执行 DROP SCHEMA public CASCADE;，重启后端。
返回 401 Not authenticated	前端没带 Token / Token过期	浏览器 F12 -> Console 输入 localStorage.clear()，重新登录。
返回 403 Forbidden	角色权限不足	检查当前接口是否要求商户身份，是否在 Headers 带了 X-Active-Role。
前端一直转圈 / 网络报错	后端挂了 / CORS 跨域	检查终端后端是否在 8888 运行；检查 vite.config.js 代理是否指向 127.0.0.1:8888。
频繁点击看广告提示“请求过于频繁”	Redis 防刷锁生效（10秒内防重）	属于正常业务逻辑保护，等待 10 秒后再点。
小程序/App 切页面白屏	分包体积过大 / 渲染慢	已加入全局 wx.showLoading，业务代码内切换路由前加入 window.$toast('加载中')。
六、 多端演进与打包 (Uni-app/小程序)
主包体积控制：主包（Login、Home、Find）必须控制在 2MB 以内。

分包策略：Merchant、Provider、Worker的二级页面必须放入独立 subPackages。

广告接入：

H5/小程序：接入微信流量主，通过条件编译 #ifdef MP-WEIXIN。

App：必须用 nvue 或原生插件桥接穿山甲（GroMore）SDK。严禁纯 H5 套壳渲染广告。

S2S验证：后端已实现 /api/ads/watch-ad 防刷接口，客户端绝不信任前端回调，必须由后端验签后发积分。

七、 上线/发版检查清单 (Checklist)
□ 前后端代码 git push 到 main 分支。
□ FastAPI Cloud / Vercel 等平台自动构建无报错。
□ 环境变量 DATABASE_URL 和 SECRET_KEY 已在云平台配置。
□ 测试环境跑通主流程：登录 -> 发岗 -> 投递 -> 录用。
□ 清理所有 console.log 和前端测试用的 alert。
□ 确保代码中 没有 包含任何真实的数据库密码或隐私密钥。