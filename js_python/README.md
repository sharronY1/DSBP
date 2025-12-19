# DSBP - Digital Software Building Platform

A modern project management platform with kanban-style task management, multi-user collaboration, comment system, and real-time notifications.

## Features

- ✅ **User Authentication** - JWT-based registration and login
- ✅ **Project Management** - Create and manage projects with visibility controls (public/private/selected users)
- ✅ **Kanban Task Board** - Organize tasks in columns: New Task, Planned, In Progress, Completed
- ✅ **Task Management** - Full CRUD operations with due dates, descriptions, and status tracking
- ✅ **Multi-user Assignment** - Assign tasks to multiple team members
- ✅ **Task Dependencies** - Define dependencies between tasks with cycle detection
- ✅ **Comment System** - Add comments to tasks with @mention support
- ✅ **Notification Center** - Real-time notifications for mentions and task updates
- ✅ **Task Activity History** - Track all task changes and activities
- ✅ **User Permissions** - Fine-grained access control for projects and tasks

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vanilla JavaScript + HTML5 + CSS3
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Testing**: pytest

## Quick Start

### 0. Environment Configuration

Create a `.env` file in the project root directory (not committed to version control):

```bash
DATABASE_URL=sqlite:///./data/dsbp.db
SECRET_KEY=CHANGE_ME_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> ⚠️ The `.env` file is ignored by default. Ensure it doesn't contain sensitive information before committing.

### 1. Install Dependencies

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Application

```bash
# Windows - Double-click or run
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh

# Or manually start
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the Application

- **Homepage**: http://localhost:8000
- **Register**: http://localhost:8000/register
- **API Documentation**: http://localhost:8000/docs

## User Guide

### First Time Setup

1. **Register Account** - Visit `/register` to create a new account
2. **Login** - Use your username and password to log in
3. **Create Project** - Click the "+" button in the left sidebar to create a project
4. **Add Tasks** - Click "+ Add Task" at the top to add tasks to your project
5. **Manage Tasks** - Click on task cards to view details and edit

### Main Operations

| Feature | How to Use |
|---------|------------|
| Create Project | Click "+" button in left sidebar |
| Add Task | Click "+ Add Task" button at the top |
| View Task Details | Click on a task card |
| Change Task Status | Select status in task details panel |
| Assign Users | Task Details → Assignees → + Add |
| Set Due Date | Task Details → Due date |
| Add Comment | Input box at bottom of task details |
| @Mention Users | Type @username in comments |
| Create Dependency | Task Details → Dependencies → Add |

### User Selector

When assigning tasks or sharing projects:
- **All Users Option** - Check to automatically select all users
- **Search Function** - Type username or email to quickly find users
- **Multi-select Support** - Select multiple users at once

## Project Structure

```
js_python/
├── main.py                 # FastAPI application entry point
├── app/                    # Backend application
│   ├── api/
│   │   └── routes.py       # API route definitions
│   ├── core/
│   │   ├── app.py          # Application factory and middleware
│   │   ├── config.py       # Configuration constants
│   │   └── database.py     # Database configuration
│   ├── models/
│   │   └── __init__.py     # SQLAlchemy models (User, Project, Task, etc.)
│   ├── schemas/
│   │   └── __init__.py     # Pydantic validation schemas
│   ├── services/
│   │   └── auth.py         # Authentication and authorization logic
│   ├── static/             # Backend static resources (placeholder)
│   └── templates/          # Template placeholder
├── frontend/               # Frontend resources
│   ├── public/             # Directly served HTML files
│   │   ├── index.html
│   │   ├── login.html
│   │   └── register.html
│   └── src/                # JS/CSS source files
│       ├── components/     # Reusable components
│       ├── pages/          # Page-specific scripts
│       └── assets/
│           └── styles/     # Stylesheet files
├── data/
│   └── dsbp.db             # SQLite database (created automatically)
├── tests/                  # Automated tests
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── factories.py        # Test data factories
│   ├── test_api.py         # API tests
│   └── test_endpoints.py   # Endpoint tests
├── start.bat / start.sh    # Startup scripts
├── reset_db.bat / reset_db.sh  # Database reset scripts
└── requirements.txt        # Python dependencies
```

> ⚠️ The `.env` file is excluded from the repository for security. Please create it manually as described above.

## API Documentation

Once the server is running, visit: http://localhost:8000/docs

### Main Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /projects` - Get project list
- `POST /projects` - Create project
- `GET /projects/{id}/tasks` - Get task list for a project
- `POST /tasks` - Create task
- `PATCH /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `POST /tasks/{id}/dependencies` - Create task dependency
- `DELETE /tasks/{id}/dependencies/{dep_id}` - Remove task dependency
- `POST /comments` - Add comment
- `GET /notifications` - Get notifications
- `PATCH /notifications/{id}` - Mark notification as read

## Database Management

### Update Database Schema

The latest version includes a `task_activities` table for tracking task history. If you encounter "table does not exist" errors after upgrading the code, stop the server and run the reset script:

```bash
reset_db.bat   # Windows
./reset_db.sh  # Linux/Mac
```

⚠️ **Warning**: Resetting the database will clear all current SQLite data. Please backup `data/dsbp.db` before using in production.

### Reset Database

```bash
# Stop the server (Ctrl+C)
# Run reset script
reset_db.bat  # Windows
./reset_db.sh  # Linux/Mac
```

### Backup Database

```bash
# Windows
copy data\dsbp.db data\dsbp_backup.db

# Linux/Mac
cp data/dsbp.db data/dsbp_backup.db
```

### Inspect Database

```bash
# Using sqlite3
sqlite3 data/dsbp.db

# View table structure
.schema tasks

# View data
SELECT * FROM tasks;

# Exit
.quit
```

## Testing

The project includes pytest-based tests. The test structure is organized as follows:

- `tests/unit/` - Unit tests for pure functions and lightweight logic (cycle detection, mention parsing, input validation)
- `tests/integration/` - Integration tests using FastAPI TestClient with temporary databases for API, permissions, and transaction behavior

### Key Test Fixtures

- `db_session` - Starts a transaction for each test and rolls back on teardown for isolation
- `client` - Wraps TestClient with optional JWT injection
- `user_factory` / `project_factory` / `task_factory` - Quick data generation for tests

### Test Priorities

1. **Dependency Graph** - Cycle detection, edge creation/deletion, cross-project validation
2. **Authentication & Authorization** - Unauthenticated access, privilege escalation, token validation
3. **API Input Validation** - Field validation, enum checks, date formats
4. **Database Constraints** - Cascading deletes, unique constraints, transaction rollback
5. **Notifications & Mentions** - Mention parsing, notification creation, XSS protection

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app
```

## Troubleshooting

### ❌ Error: "table tasks has no column named due_date"

**Cause**: Database is using an old schema

**Solution**:
```bash
# Windows
reset_db.bat

# Linux/Mac
./reset_db.sh
```

⚠️ **Note**: Resetting the database will clear all data

### ❌ Port Already in Use (Address already in use)

**Solution**: Change the port
```bash
uvicorn main:app --reload --port 8001
```

### ❌ Blank Page After Login

**Solution**:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Force refresh (Ctrl+F5)
3. Check browser Console for errors
4. Verify backend service is running

### ❌ ModuleNotFoundError

**Solution**:
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

## Security Recommendations

⚠️ **Before deploying to production, you MUST**:

1. **Change Secret Key** - Update `SECRET_KEY` in `.env` file
2. **Use Production Database** - Switch to PostgreSQL or MySQL
3. **Enable HTTPS** - Use a reverse proxy (Nginx)
4. **Configure CORS** - Restrict allowed origins
5. **Environment Variables** - Use `.env` file for all sensitive information
6. **Input Validation** - Ensure all user inputs are validated and sanitized
7. **Rate Limiting** - Implement rate limiting for API endpoints

## Development

### Code Changes

- **Backend**: Using `--reload` parameter will automatically reload on changes
- **Frontend**: Refresh browser to see changes

### View Logs

```bash
# Detailed logs
uvicorn main:app --reload --log-level debug

# Save to file
uvicorn main:app --reload > logs.txt 2>&1
```

## Best Practices

### Project Organization

- Create projects by product/feature
- Use clear, descriptive names
- Set appropriate visibility permissions

### Task Management

- Keep task titles concise and clear
- Set due dates for important tasks
- Update task status regularly
- Assign tasks to specific team members

### Team Collaboration

- Use comments to discuss details
- @mention relevant team members
- Check notifications regularly
- Keep task information up to date

## License

This project is for learning and demonstration purposes only.

## Changelog

### v1.0.0 (2025-11-16)
- ✅ Initial release
- ✅ Complete project and task management functionality
- ✅ Kanban board view and task detail panel
- ✅ Multi-user collaboration and notification system
- ✅ Task dependency management with cycle detection
- ✅ Task activity history tracking

---

**Need Help?** Check the API documentation: http://localhost:8000/docs
