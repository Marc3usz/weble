# Frontend Testing Guide

Quick reference for using the WEBLE backend testing interface.

## Quick Start (2 Steps)

### 1. Start the Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000` and show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Open the Testing Interface
Simply open the HTML file in your browser:
```
frontend/index.html
```

That's it! No npm install, no build process needed.

## Testing Interface Features

### 1. **Health Check**
- **Button**: "Check Health"
- **Purpose**: Verify backend is running
- **Expected Result**: Green status badge showing "Healthy"

### 2. **Run All Tests**
- **Button**: "All Tests"
- **Purpose**: Execute entire test suite
- **Expected Result**: 
  - Shows test summary (passed/failed counts)
  - Lists all test results with status badges
  - Requires pytest to be installed

### 3. **Run Specific Test Module**
- **Dropdown**: Select test module
- **Options**:
  - `test_step_loader` - STEP file loading and parsing
  - `test_parts_extractor` - Part extraction and classification
  - `test_svg_generator` - SVG drawing generation
  - `test_assembly_generator` - Assembly instruction generation
  - `test_api_endpoints` - API endpoint validation
- **Purpose**: Test specific pipeline stage
- **Expected Result**: Results for selected module only

### 4. **Upload & Process STEP File**
- **Button**: "Choose File"
- **Purpose**: Upload a STEP/STP file for processing
- **Supported Formats**: `.step`, `.stp`
- **Expected Result**: 
  - File metadata displayed
  - Processing pipeline executed
  - Results shown in real-time

## Interface Layout

```
┌─────────────────────────────────────────────────┐
│     WEBLE Backend Testing Interface             │
│        (AI-Powered STEP to IKEA)                │
└─────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐
│  Health & Status │  │  Test Execution  │
│  - Check Health  │  │  - All Tests     │
│  - Detailed Info │  │  - By Module     │
└──────────────────┘  └──────────────────┘

┌──────────────────────────────────────────────┐
│         File Upload & Processing             │
│    - Upload STEP files                       │
│    - View processing results                 │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│           Test Results Display               │
│    - Status badges (passed/failed/error)     │
│    - Test details and logs                   │
│    - Real-time updates                       │
└──────────────────────────────────────────────┘
```

## Status Badges

- 🟢 **Passed** (Green) - Test executed successfully
- 🔴 **Failed** (Red) - Test did not pass
- 🟡 **Error** (Yellow) - Test encountered an error
- ⚫ **Pending** (Gray) - Test not yet run
- ⚪ **Healthy** (Blue) - Service is running

## Keyboard Shortcuts

- `Ctrl+P` - Show available actions (in OpenCode CLI)
- `Escape` - Close result panels

## Troubleshooting

### Backend Not Responding
**Symptom**: "Unable to connect to backend" error
**Solution**: 
1. Ensure backend server is running on port 8000
2. Check for firewall blocking localhost:8000
3. Try `http://127.0.0.1:8000` instead of `http://localhost:8000`

### Tests Not Running
**Symptom**: Test buttons show "pytest not installed" message
**Solution**:
1. Install pytest in your Python environment:
   ```bash
   cd backend
   pip install pytest pytest-asyncio
   ```
2. Or use the infrastructure status endpoint to see what's available

### STEP File Not Processing
**Symptom**: File upload fails or shows error
**Solution**:
1. Ensure file is valid STEP/STP format
2. Check file size (max 50 MB recommended)
3. Check backend logs for detailed error messages

## Development Notes

- **Backend Infrastructure**: The testing interface communicates with 4 temporary API endpoints under `/api/v1/health/*`
- **Mock Services**: All pipeline stages return mock data for infrastructure testing
- **Test Coverage**: 50+ tests across 5 test modules
- **Real Implementation**: Mock services will be replaced with real implementations during development

## Next Steps

1. ✅ Verify backend connectivity
2. ✅ Run health check
3. ✅ Execute test suite
4. ✅ Upload test STEP files
5. Next: Implement real pipeline stages (replace mock services)

## Files Reference

```
frontend/index.html              # Main testing interface (you are here)
backend/app/api/v1/endpoints/health.py  # Health check & test endpoints
backend/tests/                   # Test modules
```

## For More Information

- See `TESTING_IMPLEMENTATION.md` for technical test details
- See `TESTING_SESSION_SUMMARY.md` for session notes
- See `README.md` for full project documentation
