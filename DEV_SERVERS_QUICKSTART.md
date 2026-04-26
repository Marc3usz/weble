# How to Run WEBLE Dev Servers

## Quick Start Commands

Open **2 terminal windows** and run these commands:

### Terminal 1: Backend Server (FastAPI on port 8000)

```powershell
cd "C:\Users\gibbo\faggy tymek\weble\backend"
.venv\Scripts\Activate.ps1
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2: Frontend Server (Next.js on port 3000)

```powershell
cd "C:\Users\gibbo\faggy tymek\weble\frontend"
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 16.2.4
  - Local:        http://localhost:3000
  ✓ Ready in 2.5s
```

---

## Detailed Setup Instructions

### Step 1: Backend Setup

```powershell
# Navigate to backend directory
cd "C:\Users\gibby\faggy tymek\weble\backend"

# Activate virtual environment (already created with uv)
.venv\Scripts\Activate.ps1

# Install/sync all dependencies (including reportlab for PDF)
uv sync

# Verify PDF dependencies installed
uv pip list | findstr reportlab

# Start dev server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**What `--reload` does:**
- Automatically restarts server when you edit Python files
- Great for development but don't use in production

**Ports:**
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`

---

### Step 2: Frontend Setup

```powershell
# Navigate to frontend directory
cd "C:\Users\gibbo\faggy tymek\weble\frontend"

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**What happens:**
- Next.js compiles TypeScript automatically
- Hot module reloading (changes appear instantly)
- Accessible at `http://localhost:3000`

---

## Environment Configuration

### Backend (.env file)

The backend uses `.env.example`. Copy it:

```powershell
cd "C:\Users\gibbo\faggy tymek\weble\backend"
cp .env.example .env
```

**Key settings for development:**

```env
# Server
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database (use memory for dev, no persistence needed)
DATABASE_TYPE=memory
DATABASE_URL=

# File upload
MAX_FILE_SIZE_MB=50

# Timeouts (in seconds)
STEP_PROCESSING_TIMEOUT_SECONDS=300
SVG_GENERATION_TIMEOUT_SECONDS=60
ASSEMBLY_GENERATION_TIMEOUT_SECONDS=120
```

### Frontend (.env.local)

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This tells the frontend where the backend API is running.

---

## Complete Startup Sequence

### First Time Setup

```powershell
# Terminal 1: Backend
cd "C:\Users\gibbo\faggy tymek\weble\backend"
.venv\Scripts\Activate.ps1
uv sync                    # Install dependencies
cp .env.example .env       # Create config
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (in another terminal)
cd "C:\Users\gibbo\faggy tymek\weble\frontend"
npm install                # Install dependencies (one time)
cp .env.example .env.local # If needed
npm run dev
```

### Subsequent Startups

**Terminal 1:**
```powershell
cd "C:\Users\gibbo\faggy tymek\weble\backend"
.venv\Scripts\Activate.ps1
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2:**
```powershell
cd "C:\Users\gibbo\faggy tymek\weble\frontend"
npm run dev
```

---

## Testing the Setup

### Is Backend Running?

```powershell
# In PowerShell, test API
Invoke-WebRequest http://localhost:8000/api/v1/health

# Or visit in browser
http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "API is healthy"
}
```

### Is Frontend Running?

```powershell
# Visit in browser
http://localhost:3000
```

Should see the WEBLE upload page.

### Test PDF Export Endpoint

```powershell
# Check endpoint is registered
Invoke-WebRequest http://localhost:8000/docs
# Look for POST /api/v1/step/export-pdf
```

---

## Useful Commands

### Backend Development

```powershell
cd "C:\Users\gibbo\faggy tymek\weble\backend"
.venv\Scripts\Activate.ps1

# Run tests
uv run pytest tests/ -v

# Format code
uv run black app/ tests/

# Lint code
uv run ruff check app/ tests/

# Type checking
uv run mypy app/

# Run specific test
uv run pytest tests/test_api_endpoints.py -v
```

### Frontend Development

```powershell
cd "C:\Users\gibbo\faggy tymek\weble\frontend"

# Format code
npm run lint

# Build for production
npm run build

# Run production build
npm start
```

---

## Troubleshooting

### Backend won't start

**Error: "Module not found: reportlab"**
```powershell
cd "C:\Users\gibbo\faggy tymek\weble\backend"
uv sync  # Reinstall dependencies
```

**Error: "Port 8000 already in use"**
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Or use different port
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend won't start

**Error: "Cannot find module 'next'"**
```powershell
cd "C:\Users\gibbo\faggy tymek\weble\frontend"
npm install  # Reinstall node_modules
```

**Error: "Port 3000 already in use"**
```powershell
# Next.js will try 3001, 3002, etc automatically
# Or kill process using 3000
netstat -ano | findstr :3000
```

### Frontend can't reach API

**Error: "Failed to fetch from http://localhost:8000"**

1. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
2. Verify backend is running on port 8000
3. Check browser console (F12) for CORS errors
4. Backend logs should show the request

---

## Typical Development Workflow

```
1. Start backend:     Terminal 1 → runs on 8000
2. Start frontend:    Terminal 2 → runs on 3000
3. Open browser:      http://localhost:3000
4. Edit files:        Changes auto-reload on both
5. View API docs:     http://localhost:8000/docs
6. Test PDF export:   Upload file → Assembly page → Click "PDF Wszystkie"
7. Check backend logs: See requests and PDF generation progress
```

---

## Hot Reload Examples

### Backend (Auto-reload enabled)
```
1. Edit: app/services/pdf_generator.py
2. Save: Server detects change (watch files)
3. Auto-restart: uvicorn restarts in ~2s
4. Test: Changes are live, no manual restart
```

### Frontend (Hot Module Replacement)
```
1. Edit: frontend/components/custom/AssemblyPageContent.tsx
2. Save: Next.js detects change
3. Browser updates: Component reloads (1-2s)
4. State preserved: Your data/inputs stay the same
```

---

## Performance Tips

### Backend
- First startup may take 30-60s (CadQuery compilation)
- Subsequent startups are fast (~5s)
- PDF generation: 1-5s depending on content
- Use `--reload` for development only

### Frontend
- First startup: 15-30s (TypeScript compilation)
- Subsequent hot-reloads: <2s
- Build for production: ~30s

---

## Stopping the Servers

**Terminal 1 (Backend):**
```
Press: Ctrl + C
```

**Terminal 2 (Frontend):**
```
Press: Ctrl + C
```

---

## Advanced: Running Both in One Terminal (Optional)

If you want to run both in one terminal:

```powershell
# Start backend in background
cd "C:\Users\gibbo\faggy tymek\weble\backend"
.venv\Scripts\Activate.ps1
$backend = Start-Process -NoNewWindow -PassThru -FilePath "uv" -ArgumentList "run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start frontend
cd "C:\Users\gibbo\faggy tymek\weble\frontend"
npm run dev

# To stop: kill $backend and press Ctrl+C for frontend
```

**Note:** Not recommended - better to use 2 terminals for debugging.

---

## Next: Testing PDF Export

Once both servers are running:

1. Go to `http://localhost:3000`
2. Upload a STEP file
3. Wait for processing to complete
4. Click "PDF Wszystkie" button
5. PDF downloads automatically!

---

**Last Updated:** April 26, 2026
**Status:** Ready for development ✅
