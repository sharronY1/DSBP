# DSBP API 文档

本文档详细说明DSBP后端API的所有端点。

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: `application/json`

## 认证

所有需要认证的端点都需要在请求头中包含JWT token：

```
Authorization: Bearer <your_access_token>
```

## 端点列表

### 认证端点

#### 注册用户

```http
POST /api/auth/register
```

**请求体**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Full Name"
}
```

**响应** (201):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "role": "user",
    "license_type": "free",
    "is_active": true,
    "is_email_verified": false,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login_at": null
  }
}
```

#### 用户登录

```http
POST /api/auth/login
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应** (200): 同注册响应

#### 获取当前用户

```http
GET /api/auth/me
```

**响应** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "role": "user",
  "license_type": "free",
  "is_active": true,
  "is_email_verified": false,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T12:00:00Z"
}
```

### 项目端点

#### 获取所有项目

```http
GET /api/projects
```

**响应** (200):
```json
[
  {
    "id": 1,
    "name": "My Project",
    "description": "Project description",
    "owner_id": 1,
    "is_archived": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 创建项目

```http
POST /api/projects
```

**请求体**:
```json
{
  "name": "New Project",
  "description": "Project description"
}
```

**响应** (201): 项目对象

#### 获取项目详情

```http
GET /api/projects/{project_id}
```

**响应** (200): 项目对象

#### 更新项目

```http
PATCH /api/projects/{project_id}
```

**请求体**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_archived": false
}
```

**响应** (200): 更新后的项目对象

#### 删除项目

```http
DELETE /api/projects/{project_id}
```

**响应** (204): 无内容

### 任务板端点

#### 获取项目的所有任务板

```http
GET /api/task-boards/project/{project_id}
```

**响应** (200):
```json
[
  {
    "id": 1,
    "name": "Sprint 1",
    "project_id": 1,
    "position": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 创建任务板

```http
POST /api/task-boards
```

**请求体**:
```json
{
  "name": "New Board",
  "project_id": 1,
  "position": 0
}
```

**响应** (201): 任务板对象

**错误响应** (403):
```json
{
  "detail": "You have reached the limit of 3 boards for free users. Please upgrade to create more boards."
}
```

#### 获取任务板详情

```http
GET /api/task-boards/{board_id}
```

**响应** (200): 任务板对象

#### 更新任务板

```http
PATCH /api/task-boards/{board_id}
```

**请求体**:
```json
{
  "name": "Updated Board Name",
  "position": 1
}
```

**响应** (200): 更新后的任务板对象

#### 删除任务板

```http
DELETE /api/task-boards/{board_id}
```

**响应** (204): 无内容

### 任务端点

#### 获取任务板的所有任务

```http
GET /api/tasks/board/{board_id}
```

**查询参数**:
- `status_filter` (可选): `todo`, `in_progress`, `done`

**响应** (200):
```json
[
  {
    "id": 1,
    "title": "Task Title",
    "description": "Task description",
    "status": "todo",
    "board_id": 1,
    "position": 0,
    "created_by_id": 1,
    "assigned_to_id": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 创建任务

```http
POST /api/tasks
```

**请求体**:
```json
{
  "title": "New Task",
  "description": "Task description",
  "status": "todo",
  "board_id": 1,
  "position": 0,
  "assigned_to_id": null
}
```

**响应** (201): 任务对象

#### 获取任务详情

```http
GET /api/tasks/{task_id}
```

**响应** (200): 任务对象

#### 更新任务

```http
PATCH /api/tasks/{task_id}
```

**请求体**:
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "status": "in_progress",
  "position": 1,
  "assigned_to_id": 2
}
```

**响应** (200): 更新后的任务对象

#### 删除任务

```http
DELETE /api/tasks/{task_id}
```

**响应** (204): 无内容

### 邀请端点

#### 创建邀请

```http
POST /api/invitations
```

**请求体**:
```json
{
  "email": "invitee@example.com",
  "project_id": 1
}
```

**响应** (201):
```json
{
  "id": 1,
  "email": "invitee@example.com",
  "project_id": 1,
  "inviter_id": 1,
  "is_accepted": false,
  "expires_at": "2024-01-08T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 获取项目的所有邀请

```http
GET /api/invitations/project/{project_id}
```

**响应** (200): 邀请对象数组

#### 接受邀请

```http
POST /api/invitations/accept/{token}
```

**响应** (200):
```json
{
  "message": "Invitation accepted successfully"
}
```

## 错误响应

所有错误响应都遵循以下格式：

```json
{
  "detail": "Error message"
}
```

### 常见HTTP状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 删除成功，无返回内容
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或token无效
- `403 Forbidden`: 无权限访问
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 验证错误
- `500 Internal Server Error`: 服务器错误

## 数据模型

### User (用户)

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "role": "user" | "admin",
  "license_type": "free" | "paid",
  "is_active": true,
  "is_email_verified": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T12:00:00Z"
}
```

### Project (项目)

```json
{
  "id": 1,
  "name": "Project Name",
  "description": "Description",
  "owner_id": 1,
  "is_archived": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### TaskBoard (任务板)

```json
{
  "id": 1,
  "name": "Board Name",
  "project_id": 1,
  "position": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Task (任务)

```json
{
  "id": 1,
  "title": "Task Title",
  "description": "Description",
  "status": "todo" | "in_progress" | "done",
  "board_id": 1,
  "position": 0,
  "created_by_id": 1,
  "assigned_to_id": 2,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Invitation (邀请)

```json
{
  "id": 1,
  "email": "invitee@example.com",
  "project_id": 1,
  "inviter_id": 1,
  "is_accepted": false,
  "expires_at": "2024-01-08T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 交互式API文档

启动后端服务后，可以访问以下URL查看交互式API文档：

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

这些文档提供了：
- 所有端点的详细说明
- 请求/响应示例
- 在线测试功能
- Schema定义

## 示例代码

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# 登录
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# 获取项目
headers = {"Authorization": f"Bearer {token}"}
projects = requests.get(f"{BASE_URL}/projects", headers=headers).json()
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api';

// 登录
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();

// 获取项目
const projectsResponse = await fetch(`${BASE_URL}/projects`, {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const projects = await projectsResponse.json();
```

### cURL

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 获取项目（使用返回的token）
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 速率限制

当前版本没有实施速率限制，但建议：

- 避免过于频繁的请求
- 使用合理的缓存策略
- 批量操作时使用适当的延迟

## 版本控制

当前API版本: **v1**

API版本通过URL路径标识：`/api/v1/...`

未来版本将保持向后兼容，或通过版本号区分。

## 支持

如有API相关问题，请：

1. 查看交互式文档
2. 检查错误响应详情
3. 查看后端日志
4. 创建Issue报告问题

