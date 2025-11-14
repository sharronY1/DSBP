# DSBP - Development Software Board Platform

DSBP是一个基于Web的软件开发管理流程软件，类似于Kanban看板系统。它提供了任务分解板（Task Decomposition Board）功能，帮助团队协作管理项目任务。

## 主要特性

- ✅ **用户认证和许可证管理**
  - 免费用户可以使用3个任务板（Task Board）
  - 付费用户无限制使用任务板
  - 基于JWT的认证系统

- ✅ **项目空间管理**
  - 创建和管理项目
  - 通过Email邀请团队成员加入项目空间
  - 项目成员权限管理

- ✅ **任务分解板（Task Decomposition Board）**
  - 三个状态：TODO、In Progress、DONE
  - 在同一项目空间内的用户可以添加、删除和更新任务
  - 任务可以分配给团队成员

- ✅ **PostgreSQL数据库**
  - 完整的用户信息管理
  - 项目、任务板、任务数据持久化

- ✅ **清晰的用户界面**
  - 基于React的现代化前端
  - 响应式设计

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI** - 现代、快速的Web框架
- **SQLAlchemy** - ORM
- **PostgreSQL** - 数据库
- **Alembic** - 数据库迁移
- **JWT** - 认证

### 前端
- **React 18**
- **Vite** - 构建工具
- **Redux** - 状态管理
- **React Router** - 路由

## 项目结构

```
DSBP/
├── backend/                 # Python后端
│   ├── api/                 # API路由
│   │   └── v1/              # API v1版本
│   ├── models/               # 数据库模型
│   ├── schemas/              # Pydantic schemas
│   ├── utils/                # 工具函数
│   ├── db/                   # 数据库工具
│   ├── config.py             # 配置
│   ├── database.py           # 数据库连接
│   └── main.py               # 应用入口
├── client/                   # React前端
│   └── src/
│       ├── api/              # API客户端
│       ├── components/       # React组件
│       └── ...
├── alembic/                  # 数据库迁移
├── requirements.txt          # Python依赖
├── env.example               # 环境变量示例
└── README.md                 # 本文档
```

## 安装和配置

### 前置要求

- Python 3.9 或更高版本
- Node.js 16 或更高版本
- PostgreSQL 12 或更高版本
- npm 或 yarn

### 1. 克隆项目

```bash
cd DSBP
```

### 2. 设置Python环境

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
```

### 3. 配置数据库

创建PostgreSQL数据库：

```sql
CREATE DATABASE dsbp_db;
CREATE USER dsbp_user WITH PASSWORD 'dsbp_password';
GRANT ALL PRIVILEGES ON DATABASE dsbp_db TO dsbp_user;
```

### 4. 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置以下配置：

```env
# 数据库配置
DATABASE_URL=postgresql://dsbp_user:dsbp_password@localhost:5432/dsbp_db

# JWT密钥（生产环境请使用强密钥）
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# 应用配置
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Email配置（用于发送邀请）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@dsbp.com
```

### 5. 初始化数据库

```bash
# 创建数据库表
python -m backend.db.init_db

# 创建管理员用户（可选）
python -m backend.db.create_admin admin@example.com admin password123
```

### 6. 设置前端

```bash
cd client

# 安装依赖
npm install

# 创建环境变量文件
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
```

## 运行应用

### 开发模式

**后端：**

```bash
# 在项目根目录
python run.py
```

后端将在 `http://localhost:8000` 运行

**前端：**

```bash
cd client
npm run dev
```

前端将在 `http://localhost:5173` 运行

### 生产模式

**构建前端：**

```bash
cd client
npm run build
```

**运行后端（生产模式）：**

```bash
# 设置环境变量
export DEBUG=False

# 运行
python run.py
```

## API文档

启动后端后，访问以下URL查看API文档：

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 主要API端点

### 认证

- `POST /api/auth/register` - 注册新用户
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 项目

- `GET /api/projects` - 获取所有项目
- `POST /api/projects` - 创建项目
- `GET /api/projects/{id}` - 获取项目详情
- `PATCH /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目

### 任务板

- `GET /api/task-boards/project/{project_id}` - 获取项目的所有任务板
- `POST /api/task-boards` - 创建任务板
- `GET /api/task-boards/{id}` - 获取任务板详情
- `PATCH /api/task-boards/{id}` - 更新任务板
- `DELETE /api/task-boards/{id}` - 删除任务板

### 任务

- `GET /api/tasks/board/{board_id}` - 获取任务板的所有任务
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PATCH /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

### 邀请

- `POST /api/invitations` - 创建并发送邀请
- `GET /api/invitations/project/{project_id}` - 获取项目的所有邀请
- `POST /api/invitations/accept/{token}` - 接受邀请

## 使用指南

### 1. 注册和登录

1. 访问前端应用
2. 点击"注册"创建新账户
3. 填写邮箱、用户名和密码
4. 注册成功后自动登录

### 2. 创建项目

1. 登录后，点击"创建项目"
2. 输入项目名称和描述
3. 点击"创建"

### 3. 创建任务板

1. 在项目页面，点击"创建任务板"
2. 输入任务板名称
3. 注意：免费用户最多创建3个任务板

### 4. 添加任务

1. 在任务板中，点击"添加任务"
2. 输入任务标题和描述
3. 选择任务状态（TODO、In Progress、DONE）
4. 可选：分配给团队成员

### 5. 邀请团队成员

1. 在项目设置中，点击"邀请成员"
2. 输入要邀请的邮箱地址
3. 系统会发送邀请邮件
4. 被邀请用户点击邮件中的链接接受邀请

### 6. 管理任务

- **移动任务状态**：拖拽任务卡片到不同的状态列
- **编辑任务**：点击任务卡片进行编辑
- **删除任务**：在任务详情中点击删除

## 许可证管理

### 免费用户

- 最多创建3个任务板
- 可以加入无限数量的项目（作为成员）
- 所有基本功能可用

### 付费用户

- 无限制创建任务板
- 所有功能可用
- 优先支持

要升级到付费版本，请联系管理员。

## 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 创建新的迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 故障排除

### 数据库连接错误

- 检查PostgreSQL服务是否运行
- 验证 `.env` 文件中的 `DATABASE_URL` 配置
- 确认数据库用户权限

### 认证错误

- 检查JWT_SECRET_KEY是否设置
- 确认token未过期
- 清除浏览器localStorage中的token

### Email发送失败

- 检查SMTP配置
- 对于Gmail，需要使用应用专用密码
- 检查防火墙设置

## 开发指南

### 添加新的API端点

1. 在 `backend/api/v1/` 创建新的路由文件
2. 在 `backend/schemas/` 定义请求/响应模型
3. 在 `backend/models/` 定义数据库模型（如需要）
4. 在 `backend/api/v1/__init__.py` 注册路由

### 前端开发

前端代码位于 `client/` 目录。主要结构：

- `src/api/` - API客户端
- `src/components/` - React组件
- `src/store/` - Redux store和reducers

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。

## 支持

如有问题或建议，请创建Issue。

## 更新日志

### v1.0.0 (2024)

- 初始版本发布
- 用户认证和许可证管理
- 项目空间管理
- 任务分解板功能
- Email邀请功能
