# WEBLE - AI-Powered STEP to IKEA Assembly Instructions

A web application that processes CAD files (STEP/STP format) representing furniture and generates IKEA-style assembly instructions with 3D visualization, 2D technical drawings, and AI-powered step guidance.

## Project Overview

WEBLE automates the generation of professional assembly instructions from CAD models. It extracts 3D geometry, classifies furniture parts, generates technical drawings, and uses AI to create intuitive step-by-step assembly guides.

## Core Features

### 1. STEP File Upload & 3D Processing

- **File Upload**: Users can upload STEP/STP files (up to 50 MB) through the web interface
- **Backend Processing**: 
  - CadQuery (OpenCASCADE-based) processes the CAD file
  - 3D geometry is extracted and triangulated for browser rendering
  - Vertices, normals, and indices are generated for Three.js visualization
- **Real-time Progress**: Server-Sent Events (SSE) stream processing updates to the frontend
- **3D Rendering**: Frontend visualizes the model using Three.js with React Three Fiber

**Endpoint**: `POST /api/step/upload`

### 2. Parts Extraction & Classification

- **Part Extraction**: Automatically extracts individual solids from STEP files
- **Classification**: Categorizes parts as:
  - Panels (large flat elements)
  - Hardware (screws, dowels, cam locks)
  - Other components
- **2D Drawings**: Generates SVG technical drawings (isometric projections in IKEA style) for each part
- **Part Grouping**: 
  - Identifies identical small parts (e.g., 12 screws of the same type)
  - Creates single drawing with quantity notation (×12)
  - Uses 15% tolerance for dimension/volume comparison

**Endpoint**: `POST /api/step/parts-2d`

### 3. Assembly Instruction Generation

- **AI-Powered Steps**: Uses Google Gemini or OpenRouter API to generate logical assembly sequences
- **Step Components**:
  - Step number and descriptive title
  - Natural language instructions
  - Referenced part indices
  - Part roles (e.g., "side panel", "dowel")
  - Context parts shown as gray outlines
- **Exploded Views**: SVG diagrams showing how parts connect in each step
- **Two Modes**:
  - `preview_only=true` - Quick full furniture overview as SVG (no step analysis)
  - `preview_only=false` - Full analysis with parts classification and AI-generated assembly steps

**Endpoint**: `POST /api/step/assembly-analysis`

**Step Structure Example**:
```json
{
  "stepNumber": 1,
  "title": "Assemble left side panel",
  "description": "Connect left side panel (A) to bottom shelf (B) using cam locks",
  "partIndices": [0, 5],
  "partRoles": {
    "0": "side panel",
    "5": "cam lock"
  },
  "contextPartIndices": []
}
```

## Tech Stack

### Frontend
- **Framework**: Next.js with TypeScript
- **3D Graphics**: Three.js, @react-three/fiber
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS (with shadcn/ui)

### Backend
- **Runtime**: Python 3.10+
- **Framework**: FastAPI
- **CAD Processing**: CadQuery (OpenCASCADE)
- **2D Graphics**: OpenCASCADE HLR (Hidden Line Removal)

### Data & Storage
- **Database**: PostgreSQL
- **ORM**: Prisma
- **File Storage**: S3-compatible storage (local disk option for development)

### AI & Third-party
- **Assembly Instructions**: OpenRouter API (Google Gemini / Claude)

## Project Structure

```
weble/
├── frontend/              # Next.js application
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # Utilities and helpers
│   └── public/           # Static assets
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models/       # Data models
│   │   └── core/         # Configuration
│   ├── prisma/           # Prisma schema
│   └── requirements.txt  # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- PostgreSQL 13+
- Git

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/weble
OPENROUTER_API_KEY=your_api_key
S3_BUCKET=weble-files
S3_ENDPOINT=http://localhost:9000  # MinIO for local dev
```

Run migrations:
```bash
cd backend
prisma migrate dev
```

Start server:
```bash
python -m uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

## API Endpoints

### POST `/api/step/upload`
Upload and process STEP file
- **Request**: Form data with `file` (STEP/STP)
- **Response**: Triangulated geometry (vertices, normals, indices) + metadata
- **Streaming**: SSE for real-time progress updates

### POST `/api/step/parts-2d`
Extract parts and generate 2D drawings
- **Request**: `{ "modelId": "uuid" }`
- **Response**: Array of parts with SVG drawings and metadata

### POST `/api/step/assembly-analysis`
Generate assembly instructions
- **Query Parameters**:
  - `preview_only` (boolean): true for quick preview, false for full analysis
- **Request**: `{ "modelId": "uuid" }`
- **Response**: Array of assembly steps with descriptions and diagrams

## Development Workflow

1. **CAD Processing**
   - CadQuery extracts geometry and generates triangulation
   - Metrics (volume, bounding box) calculated for classification

2. **Parts Management**
   - Parts stored with unique IDs
   - Similar parts grouped by volume/dimension tolerance (±15%)
   - SVG drawings generated for each unique part

3. **Assembly Generation**
   - AI analyzes part relationships and spatial arrangement
   - Generates logical assembly sequence
   - Creates exploded view diagrams for each step

## Environment Variables

### Backend
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/weble

# API Keys
OPENROUTER_API_KEY=sk_...

# Storage
S3_BUCKET=weble-files
S3_ENDPOINT=http://localhost:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Server
DEBUG=True
LOG_LEVEL=INFO
```

### Frontend
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Contributing

1. Create a feature branch: `git checkout -b feature/description`
2. Make your changes
3. Commit with conventional commits
4. Push and create a Pull Request

## License

MIT

## Contact

For questions or support, please open an issue in the repository.
