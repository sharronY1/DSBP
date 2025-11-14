# DSBP Quick Run Guide

## Prerequisites Check

Before running, make sure you have installed:
- ✅ Python 3.9+
- ✅ PostgreSQL 12+
- ✅ Node.js 16+ (if you need to run the frontend)

## Quick Run Steps

### 1. Check and Create Environment Variables File

If you don't have a `.env` file yet, copy from `env.example`:

```bash
# Windows PowerShell
Copy-Item env.example .env

# Or manually copy and rename
```

Then edit the `.env` file, at least modify:
- `DATABASE_URL` - Your PostgreSQL connection information
- `JWT_SECRET_KEY` - Generate a random string (at least 32 characters)

### 2. Setup PostgreSQL Database

If you haven't created the database yet, execute:

```sql
-- Login to PostgreSQL
psql -U postgres

-- Create database and user
CREATE DATABASE dsbp_db;
CREATE USER dsbp_user WITH PASSWORD 'dsbp_password';
GRANT ALL PRIVILEGES ON DATABASE dsbp_db TO dsbp_user;
\q
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Make sure virtual environment is activated
python -m backend.db.init_db
```

### 5. Run Backend

```bash
# In project root directory (DSBP folder)
python run.py
```

Backend will run at `http://localhost:8000`

### 6. Verify Backend is Running

Open browser and visit:
- API Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### 7. Run Frontend (Optional)

If frontend is configured:

```bash
cd client
npm install
npm run dev
```

Frontend will run at `http://localhost:5173`

## Common Issues

### Issue 1: Database Connection Failed
- Check if PostgreSQL service is running
- Verify `DATABASE_URL` in `.env` file is correct
- Confirm database user permissions

### Issue 2: Module Import Error
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue 3: Port Already in Use
- Backend default port is 8000, you can modify `PORT` in `.env`
- Frontend default port is 5173

## Next Steps

1. Visit http://localhost:8000/api/docs to view API documentation
2. Test functionality using API or run frontend application
3. Create your first user account

