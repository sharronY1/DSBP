# DSBP 安装指南

本文档提供详细的安装步骤，帮助你在本地或服务器上安装和运行DSBP。

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [验证安装](#验证安装)
5. [常见问题](#常见问题)

## 系统要求

### 操作系统

- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

### 软件要求

- **Python**: 3.9 或更高版本
- **Node.js**: 16.x 或更高版本
- **PostgreSQL**: 12 或更高版本
- **npm**: 7.x 或更高版本（或yarn）

### 硬件要求

- **内存**: 至少 2GB RAM
- **存储**: 至少 1GB 可用空间
- **CPU**: 双核或更高

## 安装步骤

### 步骤 1: 安装Python

#### Windows

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Python 3.9或更高版本
3. 运行安装程序，**勾选"Add Python to PATH"**
4. 完成安装

验证安装：
```bash
python --version
```

#### macOS

使用Homebrew：
```bash
brew install python@3.9
```

验证安装：
```bash
python3 --version
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip
```

验证安装：
```bash
python3 --version
```

### 步骤 2: 安装Node.js

#### Windows/macOS

1. 访问 [Node.js官网](https://nodejs.org/)
2. 下载LTS版本
3. 运行安装程序

#### Linux

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

验证安装：
```bash
node --version
npm --version
```

### 步骤 3: 安装PostgreSQL

#### Windows

1. 访问 [PostgreSQL官网](https://www.postgresql.org/download/windows/)
2. 下载安装程序
3. 运行安装，记住设置的postgres用户密码

#### macOS

```bash
brew install postgresql@14
brew services start postgresql@14
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 步骤 4: 设置PostgreSQL数据库

1. 登录PostgreSQL：

```bash
# Windows (使用pgAdmin或命令行)
psql -U postgres

# macOS/Linux
sudo -u postgres psql
```

2. 创建数据库和用户：

```sql
CREATE DATABASE dsbp_db;
CREATE USER dsbp_user WITH PASSWORD 'dsbp_password';
GRANT ALL PRIVILEGES ON DATABASE dsbp_db TO dsbp_user;
\q
```

### 步骤 5: 克隆或下载项目

```bash
cd /path/to/your/projects
# 如果是从git克隆
git clone <repository-url> DSBP
cd DSBP
```

### 步骤 6: 设置Python后端

1. 创建虚拟环境：

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. 安装Python依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 7: 配置环境变量

1. 复制环境变量示例文件：

```bash
# Windows
copy env.example .env

# macOS/Linux
cp env.example .env
```

2. 编辑 `.env` 文件，修改以下配置：

```env
# 数据库配置（根据你的设置修改）
DATABASE_URL=postgresql://dsbp_user:dsbp_password@localhost:5432/dsbp_db

# JWT密钥（生产环境必须更改）
JWT_SECRET_KEY=your-very-secret-key-change-this-in-production-min-32-chars

# 应用配置
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Email配置（用于发送邀请邮件）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=noreply@dsbp.com
SMTP_FROM_NAME=DSBP
```

**重要提示**：
- 对于Gmail，需要生成应用专用密码：Google账户 → 安全性 → 应用专用密码
- JWT_SECRET_KEY应该是一个长随机字符串（至少32个字符）

### 步骤 8: 初始化数据库

```bash
# 确保虚拟环境已激活
python -m backend.db.init_db
```

如果成功，你会看到：
```
Database tables created successfully!
```

### 步骤 9: 创建管理员用户（可选）

```bash
python -m backend.db.create_admin admin@example.com admin password123
```

### 步骤 10: 设置前端

1. 进入前端目录：

```bash
cd client
```

2. 安装依赖：

```bash
npm install
```

3. 创建前端环境变量：

```bash
# Windows
echo VITE_API_BASE_URL=http://localhost:8000 > .env

# macOS/Linux
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```

## 配置说明

### 后端配置 (.env)

| 配置项 | 说明 | 示例 |
|--------|------|------|
| DATABASE_URL | PostgreSQL连接字符串 | postgresql://user:pass@localhost:5432/dbname |
| JWT_SECRET_KEY | JWT签名密钥 | 随机字符串（至少32字符） |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | Token过期时间（分钟） | 1440 |
| DEBUG | 调试模式 | True/False |
| CORS_ORIGINS | 允许的CORS源 | http://localhost:3000,http://localhost:5173 |
| SMTP_HOST | SMTP服务器地址 | smtp.gmail.com |
| SMTP_PORT | SMTP端口 | 587 |
| SMTP_USER | SMTP用户名 | your-email@gmail.com |
| SMTP_PASSWORD | SMTP密码 | your-app-password |
| FREE_USER_BOARD_LIMIT | 免费用户任务板限制 | 3 |
| PAID_USER_BOARD_LIMIT | 付费用户任务板限制 | -1（无限制） |

### 前端配置 (.env)

| 配置项 | 说明 | 示例 |
|--------|------|------|
| VITE_API_BASE_URL | 后端API地址 | http://localhost:8000 |

## 验证安装

### 1. 启动后端

```bash
# 在项目根目录，确保虚拟环境已激活
python run.py
```

你应该看到类似输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. 测试API

打开浏览器访问：
- API文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

### 3. 启动前端

```bash
cd client
npm run dev
```

你应该看到：
```
  VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 4. 测试完整流程

1. 打开浏览器访问 http://localhost:5173
2. 注册新用户
3. 创建项目
4. 创建任务板
5. 添加任务

## 常见问题

### Q: 数据库连接失败

**A:** 检查以下几点：
- PostgreSQL服务是否运行：`sudo systemctl status postgresql` (Linux)
- 数据库URL是否正确
- 用户权限是否正确设置
- 防火墙是否阻止连接

### Q: 端口已被占用

**A:** 
- 后端默认端口8000，可以修改 `.env` 中的 `PORT`
- 前端默认端口5173，可以在 `client/vite.config.js` 中修改

### Q: 无法发送邮件

**A:**
- 检查SMTP配置是否正确
- Gmail需要使用应用专用密码，不是普通密码
- 检查防火墙和网络设置
- 查看后端日志中的错误信息

### Q: 前端无法连接后端

**A:**
- 检查 `VITE_API_BASE_URL` 是否正确
- 检查CORS配置
- 确认后端正在运行
- 检查浏览器控制台的错误信息

### Q: 导入错误 (ImportError)

**A:**
- 确保虚拟环境已激活
- 重新安装依赖：`pip install -r requirements.txt`
- 检查Python版本是否符合要求

### Q: npm install 失败

**A:**
- 清除npm缓存：`npm cache clean --force`
- 删除 `node_modules` 和 `package-lock.json`，重新安装
- 检查Node.js版本

## 生产环境部署

### 使用Gunicorn运行后端

```bash
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 使用Nginx作为反向代理

创建Nginx配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/DSBP/client/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 使用Docker（可选）

创建 `Dockerfile` 和 `docker-compose.yml` 可以简化部署。参考Docker文档了解更多。

## 下一步

安装完成后，请阅读：
- [README.md](README.md) - 了解主要功能
- [API文档](http://localhost:8000/api/docs) - 查看API端点
- 开始使用应用！

如有问题，请查看故障排除部分或创建Issue。

