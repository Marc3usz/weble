# WEBLE Quick Start Guide

## System Overview

WEBLE is an end-to-end system for generating furniture assembly instructions from CAD files. It consists of:

1. **Backend** (FastAPI) - Processes STEP files, extracts geometry, classifies parts, generates instructions
2. **Frontend** (Next.js) - Web UI for upload, visualization, and instruction viewing

## Quick Start (5 minutes)

### Prerequisites

- Node.js 18+ installed
- Backend running on `http://localhost:8000`

### Start Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Set environment
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start dev server
npm run dev
```

Open browser: http://localhost:3000

## User Workflow

### Step 1: Upload STEP File

1. Go to http://localhost:3000/upload
2. Drag & drop or click to select a STEP/STP file (max 50 MB)
3. Monitor real-time progress
4. Auto-redirects to 3D viewer when complete

### Step 2: Explore 3D Model

1. Interact with model:
   - **Left-click + drag**: Rotate
   - **Scroll**: Zoom
   - **Right-click + drag**: Pan
2. Click "Rozłóż na części" to extract parts
3. Or click "Instrukcja montażu" to generate assembly steps

### Step 3: Review Parts

1. See all extracted parts in grid
2. Each part shows:
   - Part type (panel, hardware, fastener, etc.)
   - Quantity (if multiple identical)
   - Volume and dimensions
3. Click "Instrukcja montażu" to proceed

### Step 4: Follow Assembly Steps

1. Read step title and description
2. See parts involved in this step
3. Review assembly sequence and tips
4. Use navigation arrows to move between steps
5. Download PDF anytime with "Eksport PDF" button

## API Endpoints

Backend provides these key endpoints:

```
POST   /api/v1/step/upload              Upload STEP file
GET    /api/v1/step/{model_id}          Get model geometry
GET    /api/v1/step/progress/{job_id}/stream   Progress SSE
POST   /api/v1/step/parts-2d            Extract parts
POST   /api/v1/step/assembly-analysis   Generate assembly steps
```

## Frontend URL Structure

```
/upload                    Upload page
/viewer/{modelId}          3D model viewer
/parts/{modelId}           Parts list
/assembly/{modelId}        Assembly instructions
```

## Common Issues

### Backend not responding

```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# If not running, start it:
cd backend
python -m uvicorn app.main:app --reload
```

### API URL not found

Frontend reads `NEXT_PUBLIC_API_URL` environment variable:
```bash
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

### 3D model not showing

- Ensure geometry was successfully extracted by backend
- Check browser console for WebGL errors
- Verify file was processed (check progress bar reached 100%)

### PDF export not working

- All parts and assembly steps must be loaded
- Check that React PDF Renderer is installed
- Try in Chrome/Chromium browser first

## Development

### File Structure

```
frontend/
├── app/
│   ├── upload/           Page: File upload
│   ├── viewer/           Page: 3D viewer
│   ├── parts/            Page: Parts list
│   ├── assembly/         Page: Instructions
│   ├── components/       Reusable components
│   ├── services/         API client
│   ├── store/            State management
│   ├── hooks/            Custom hooks
│   └── types/            TypeScript definitions
└── package.json
```

### Running Build Checks

```bash
# Type check
npm run build

# Start production server
npm run start
```

### Testing

```bash
# Create test STEP file scenarios
# Test with different file sizes
# Test error scenarios (invalid files, timeouts)
```

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Note: Variables prefixed with `NEXT_PUBLIC_` are exposed to browser.

## Next Steps

1. **Customize UI**: Edit Tailwind CSS classes in page components
2. **Add more visualizations**: Extend 3D viewer capabilities
3. **Integrate databases**: Store models and instructions persistently
4. **Add user accounts**: Implement authentication
5. **Mobile app**: Build React Native version
6. **Real-time collaboration**: Add WebSocket support

## Architecture

```
User Browser
    ↓
[Next.js Frontend] ←→ [FastAPI Backend]
    ↓
    ├→ Upload: SSE progress
    ├→ Model: Geometry 3D
    ├→ Parts: Classifications
    └→ Assembly: AI Instructions
```

## Support & Documentation

- Full docs: See `README.md` in frontend directory
- Backend docs: See `README.md` in backend directory
- Type definitions: Check `app/types/index.ts`
- API service: Check `app/services/api.ts`

## Performance Tips

1. **Reduce file size**: Simplify STEP models before upload
2. **Use Chrome**: Best WebGL performance
3. **Clear browser cache**: If changes don't appear
4. **Monitor memory**: Large 3D models may use significant RAM

## Security Notes

- File validation: Max 50 MB, STEP/STP format only
- API validation: All inputs validated by backend
- CORS: Configure as needed for your deployment
- No sensitive data: Keep API URLs public-safe

---

**Version**: 1.0.0  
**Last Updated**: 2024

For detailed information, see `README.md`.
