# DSBP 项目总结

## 项目概述

DSBP (Development Software Board Platform) 是一个基于Web的软件开发管理流程软件，类似于Kanban看板系统。本项目基于开源项目Planka进行重构，使用Python FastAPI重写了后端，保留了React前端框架。

## 已完成功能

### ✅ 后端实现 (Python FastAPI)

1. **用户认证系统**
   - 用户注册和登录
   - JWT token认证
   - 密码加密存储（bcrypt）
   - 用户信息管理

2. **许可证管理系统**
   - 免费用户：最多3个任务板
   - 付费用户：无限制任务板
   - 许可证验证和限制检查

3. **项目管理**
   - 创建、查看、更新、删除项目
   - 项目成员管理
   - 项目权限控制

4. **任务板管理**
   - 创建、查看、更新、删除任务板
   - 任务板与项目关联
   - 许可证限制检查

5. **任务管理**
   - 创建、查看、更新、删除任务
   - 任务状态管理（TODO, In Progress, DONE）
   - 任务分配功能

6. **Email邀请功能**
   - 通过Email邀请用户加入项目
   - 邀请链接生成和验证
   - SMTP邮件发送

7. **数据库**
   - PostgreSQL数据库集成
   - SQLAlchemy ORM
   - Alembic数据库迁移
   - 完整的数据库模型

### ✅ 前端API客户端

1. **HTTP客户端**
   - 统一的API调用接口
   - JWT token自动管理
   - 错误处理

2. **API模块**
   - 认证API
   - 项目API
   - 任务板API
   - 任务API
   - 邀请API

### ✅ 文档

1. **README.md** - 项目主文档
2. **INSTALLATION.md** - 详细安装指南
3. **USAGE.md** - 使用指南
4. **API.md** - API文档
5. **QUICKSTART.md** - 快速开始指南

## 项目结构

```
DSBP/
├── backend/                 # Python后端
│   ├── api/v1/             # API路由
│   ├── models/             # 数据库模型
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # 工具函数
│   ├── db/                 # 数据库工具
│   ├── config.py           # 配置
│   ├── database.py         # 数据库连接
│   └── main.py             # 应用入口
├── client/                 # React前端
│   └── src/api/            # API客户端
├── alembic/                # 数据库迁移
├── requirements.txt        # Python依赖
├── env.example             # 环境变量示例
└── 文档文件
```

## 技术栈

### 后端
- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT
- bcrypt
- aiosmtplib

### 前端
- React 18
- Vite
- Redux (保留结构，待实现)
- React Router (保留结构，待实现)

## 数据库模型

1. **User** - 用户表
2. **Project** - 项目表
3. **TaskBoard** - 任务板表
4. **Task** - 任务表
5. **ProjectMember** - 项目成员关联表
6. **Invitation** - 邀请表
7. **License** - 许可证统计表

## API端点

### 认证
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户

### 项目
- `GET /api/projects` - 获取所有项目
- `POST /api/projects` - 创建项目
- `GET /api/projects/{id}` - 获取项目详情
- `PATCH /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目

### 任务板
- `GET /api/task-boards/project/{project_id}` - 获取项目任务板
- `POST /api/task-boards` - 创建任务板
- `GET /api/task-boards/{id}` - 获取任务板详情
- `PATCH /api/task-boards/{id}` - 更新任务板
- `DELETE /api/task-boards/{id}` - 删除任务板

### 任务
- `GET /api/tasks/board/{board_id}` - 获取任务板任务
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PATCH /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

### 邀请
- `POST /api/invitations` - 创建邀请
- `GET /api/invitations/project/{project_id}` - 获取项目邀请
- `POST /api/invitations/accept/{token}` - 接受邀请

## 配置说明

### 环境变量

主要配置项：
- `DATABASE_URL` - 数据库连接字符串
- `JWT_SECRET_KEY` - JWT签名密钥
- `SMTP_*` - 邮件服务器配置
- `FREE_USER_BOARD_LIMIT` - 免费用户任务板限制
- `PAID_USER_BOARD_LIMIT` - 付费用户任务板限制

## 使用说明

### 启动后端

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# 运行
python run.py
```

### 启动前端

```bash
cd client
npm install
npm run dev
```

### 初始化数据库

```bash
python -m backend.db.init_db
```

### 创建管理员

```bash
python -m backend.db.create_admin email username password
```

## 与Planka的区别

1. **后端语言**: Node.js/Sails.js → Python/FastAPI
2. **变量命名**: 所有planka相关变量已重命名为dsbp相关
3. **功能简化**: 专注于任务分解板功能，移除了部分复杂功能
4. **许可证系统**: 实现了免费/付费用户的限制
5. **API设计**: RESTful API，使用FastAPI自动生成文档

## 待完善功能

1. **前端UI组件**
   - 需要基于planka的前端代码进行适配
   - 重命名所有planka相关变量
   - 连接新的Python API

2. **实时更新**
   - WebSocket支持（可选）
   - 实时任务状态同步

3. **高级功能**
   - 任务评论
   - 文件附件
   - 任务历史记录
   - 通知系统

4. **部署**
   - Docker支持
   - 生产环境配置
   - CI/CD流程

## 开发规范

### 代码风格

- Python: 遵循PEP 8
- JavaScript: 遵循Airbnb风格指南
- 使用类型提示（Python）
- 完整的文档字符串

### 数据库迁移

使用Alembic进行数据库版本控制：

```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head
```

### API版本控制

当前版本: v1

通过URL路径标识：`/api/v1/...`

## 测试

（待实现）

- 单元测试
- 集成测试
- API测试
- 前端测试

## 安全考虑

1. **密码安全**
   - 使用bcrypt加密
   - 不存储明文密码

2. **JWT安全**
   - Token过期机制
   - 安全的密钥管理

3. **SQL注入防护**
   - 使用ORM参数化查询

4. **CORS配置**
   - 限制允许的源

5. **输入验证**
   - Pydantic schema验证

## 性能优化

1. **数据库**
   - 适当的索引
   - 查询优化

2. **API**
   - 响应缓存（可选）
   - 分页支持（待实现）

3. **前端**
   - 代码分割
   - 懒加载

## 许可证

本项目采用MIT许可证。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 支持

如有问题或建议，请：

1. 查看文档
2. 搜索已有Issue
3. 创建新Issue

## 更新日志

### v1.0.0 (2024)

- ✅ 初始版本发布
- ✅ 用户认证和许可证管理
- ✅ 项目空间管理
- ✅ 任务分解板功能
- ✅ Email邀请功能
- ✅ 完整的API文档
- ✅ 详细的安装和使用文档

---

**项目状态**: 后端核心功能已完成，前端API客户端已创建，文档完整。前端UI组件需要进一步开发。

