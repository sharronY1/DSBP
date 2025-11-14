# DSBP 快速开始指南

5分钟快速启动DSBP！

## 前置要求

确保已安装：
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

## 快速安装

### 1. 设置数据库

```bash
# 登录PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE dsbp_db;
CREATE USER dsbp_user WITH PASSWORD 'dsbp_password';
GRANT ALL PRIVILEGES ON DATABASE dsbp_db TO dsbp_user;
\q
```

### 2. 配置后端

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp env.example .env

# 编辑 .env 文件，至少修改：
# - DATABASE_URL
# - JWT_SECRET_KEY (生成一个随机字符串)
```

### 3. 初始化数据库

```bash
python -m backend.db.init_db
```

### 4. 启动后端

```bash
python run.py
```

后端运行在 http://localhost:8000

### 5. 配置前端

```bash
cd client

# 安装依赖
npm install

# 创建环境变量
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```

### 6. 启动前端

```bash
npm run dev
```

前端运行在 http://localhost:5173

## 首次使用

1. 打开浏览器访问 http://localhost:5173
2. 点击"注册"创建账户
3. 登录后创建第一个项目
4. 在项目中创建任务板
5. 添加任务并开始管理！

## 验证安装

访问以下URL确认一切正常：

- 前端: http://localhost:5173
- 后端API: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

## 需要帮助？

- 详细安装指南: [INSTALLATION.md](INSTALLATION.md)
- 使用说明: [USAGE.md](USAGE.md)
- API文档: [API.md](API.md)

