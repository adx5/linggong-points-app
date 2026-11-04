
# 📖 linggong-V2 项目运维与测试执行手册

## 一、 全局架构与规范

1. **技术栈**：
   * 前端：Vue3 + Vite + Pinia（H5 移动端）。
   * 后端：FastAPI + PostgreSQL (Neon) + SQLAlchemy。
   * 云端：腾讯云 CloudBase（云托管跑后端，静态托管跑前端）。
2. **多端物理隔离**：本地终端启动时，后端必须在 `backend` 目录，前端必须在 `frontend` 目录。代码中所有的互相导入（import）严禁带 `backend.` 前缀。

## 二、 核心环境变量配置

### 1. 本地开发环境 (`backend/.env`)
在 backend 根目录下必须有 `.env` 文件（**千万别传 GitHub**）：
```env
DATABASE_URL=postgresql://neondb_owner:你的密码@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=linggong_v2_secret_2026_abcdefg
REDIS_URL=redis://localhost:6379/0
```

### 2. 【新增】云端环境 (腾讯云 CloudBase 环境变量)
在云托管 -> 服务配置 -> 环境变量中必须配置：
* `DATABASE_URL` = 必须带 `?sslmode=require`
* `SECRET_KEY` = 保持与本地一致
* `ENV` = `staging`
* `ENABLE_GUEST_MODE` = `True`
* `AUTO_FINISH_HOURS` = `0` （定时任务默认关闭）
* `ALLOW_ORIGINS` = 前端静态托管默认域名（如 `https://xxx.tcloudbaseapp.com`，**千万别带结尾斜杠 `/`**）

## 三、 本地开发启动 SOP

### 💻 后端启动 (FastAPI)
```powershell
cd E:\Code\linggong-V2\backend
# 激活虚拟环境
.\.venv\Scripts\activate
# 安装依赖（极其重要：全栈只要改了代码，必执行这句防缺包报错）
pip install -r requirements.txt
# 启动服务（端口 8888）
uvicorn main:app --reload --port 8888
```
*成功标志*：终端最后出现 `INFO: Application startup complete.`

### 📱 前端启动 (Vue3)
新开一个终端窗口：
```powershell
cd E:\Code\linggong-V2\frontend
npm install
npm run dev
```
*访问页面*：`http://localhost:5173`

## 四、 【全新核心】代码推送与云端部署 SOP

当代码本地跑通了,您必须按以下顺序操作：

### 1. 将代码推送到 GitHub
```powershell
cd E:\Code\linggong-V2
git status   # 🚨 必须检查，绝对不能看到 backend/.env
git add .
git commit -m "update: 修复xxx问题" 
git push origin main
```
*踩坑急救*：如果 `git push` 报错 `Failed to connect to github.com port 443`，说明网络被墙。请开加速器（如Watt Toolkit），或让全栈帮忙推。

### 2. 部署后端 (云托管)
1. 去 CloudBase 控制台 -> `云函数/云托管` -> `backend` 服务。
2. 点击 **`更新服务`**，选择 `main` 分支，点击 **`部署`**。
3. **必须等待状态变成绿色的`正常`**。
4. 浏览器访问 `https://backend-.../health`，返回 `{"status":"ok"}` 即成功。

### 3. 部署前端 (静态托管)
1. 本地终端进入 `frontend`，执行 `npm run build` 打包。
2. 去 CloudBase -> `静态网站托管` -> `文件管理`。
3. **删除旧文件**：勾选之前的 `assets` 文件夹和 `index.html` 点击删除。
4. **上传新文件**：打开本地 `dist` 文件夹，**全选里面的内容**（千万别传外层的dist壳），拖拽上传。
5. **检查结构**：第一层必须直接是 `index.html` 和 `assets/`。

## 五、 数据库运维 (Neon PostgreSQL)

1. **表结构未同步 (报 500 错误)**
   最快解决办法：在 Neon SQL Editor 中执行 `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`，然后重启后端让系统自动建表。
2. **清空脏测试数据**
   `TRUNCATE TABLE users, jobs, job_applications, ad_callback_log RESTART IDENTITY CASCADE;`
3. **【新增】修复测试数据 (C端查不到数据时用)**
   因为历史Bug导致数据写入错误，执行以下SQL抢救：
   ```sql
   UPDATE cooperation_entities SET status = 'active', city_id = '410185' WHERE user_id = (SELECT id FROM users WHERE phone = '13900000002');
   UPDATE jobs SET publish_status = 'active', city_id = '410185', job_type = 'long_term' WHERE merchant_id = (SELECT id FROM users WHERE phone = '13900000002');
   ```

## 六、 常见故障排查 SOP（实战版）

| 报错现象 | 根本原因 | 解决方案 |
| :--- | :--- | :--- |
| **云端部署失败，日志报 `ModuleNotFoundError`** | 全栈漏装依赖 | 让他把依赖名加到 `requirements.txt`，推上GitHub重新部署。 |
| **登录报 500 / 查表报 UndefinedColumn** | 数据库表结构未同步 | 执行 `DROP SCHEMA public CASCADE;` 重建表。 |
| **返回 401 Not authenticated** | 前端没带 Token / Token过期 | 浏览器 F12 -> Console 输入 `localStorage.clear()`，重新登录。 |
| **返回 403 Forbidden** | 角色权限不足 | 检查当前接口是否要求商户身份，是否在 Headers 带了 `X-Active-Role`。 |
| **浏览器报 CORS 跨域拦截** | 后端放行名单没配好 | 去 CloudBase 检查 `ALLOW_ORIGINS` 的域名是否带`https://`且无斜杠。 |
| **页面刷新报 404 Not Found** | 单页应用路由未配置重写 | 访问网址必须带 `#` (如 `.../#/login`)。 |
| **页面一直转圈/冷启动慢** | 云托管/Neon数据库休眠 | 免费版通病，先访问一下 `/health` 唤醒，或等10秒。 |

## 七、 多端演进与打包 (Uni-app/小程序)

1. **主包体积控制**：主包（Login、Home、Find）必须控制在 2MB 以内。
2. **分包策略**：Merchant、Provider、Worker的二级页面必须放入独立 subPackages。
3. **广告接入**：S2S验证，客户端绝不信任前端回调，必须由后端验签后发积分。
4. **【新增】现阶段小程序策略**：因为“测试号”无法发布体验版和配置业务域名，现阶段直接用手机浏览器打开 H5 链接测试即可，暂缓小程序套壳。

## 八、 上线/发版检查清单 (Checklist)

- [ ] **【运维动作】** 确认全栈本地已跑通，且已将最新代码 `git push` 到 main 分支。
- [ ] **【后端】** CloudBase 云托管点“更新服务”，状态变绿 `正常`，访问 `/health` 返回 `ok`。
- [ ] **【前端】** 本地已 `npm run build`，旧 `assets` 已删，新文件已传，且根目录有 `index.html`。
- [ ] **【环境】** 确认云端 `ALLOW_ORIGINS` 和 `DATABASE_URL` 没有配错。
- [ ] **【验收】** 浏览器按 `Ctrl + F5` 强刷，清理所有 console.log，完整走通：登录 -> 发岗 -> 投递 -> 录用。
- [ ] **【安全】** 确保代码中 没有 包含任何真实的数据库密码或隐私密钥。