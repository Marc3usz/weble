# WEBLE Frontend

AI-powered furniture assembly instructions generator. A Next.js frontend that visualizes STEP CAD files, extracts parts, and generates step-by-step assembly instructions with AI assistance.

## Overview

WEBLE is a comprehensive system for automating furniture assembly instruction generation from STEP CAD files. This frontend provides:

- **3D Model Upload & Visualization** - Upload STEP/STP files with real-time progress tracking
- **Interactive 3D Viewer** - Explore models in an IKEA-style isometric view using Three.js
- **Parts Management** - View extracted parts with classifications (panels, hardware, fasteners, etc.)
- **Assembly Instructions** - Step-by-step assembly guide with AI-generated descriptions
- **PDF Export** - Generate printable assembly manuals with diagrams and instructions

## Architecture

### Project Structure

```
app/
├── upload/               # File upload page with progress tracking
├── viewer/[modelId]/    # 3D model viewer
├── parts/[modelId]/     # Parts list and details
├── assembly/[modelId]/  # Assembly instructions carousel
├── components/          # React components
│   └── GeometryViewer.tsx    # 3D viewer with Three.js
├── services/            # API services
│   └── api.ts           # Backend API client
├── store/               # Zustand state management
│   └── appStore.ts      # Global app state
├── hooks/               # Custom React hooks
│   └── useProgress.ts   # SSE progress streaming hook
├── types/               # TypeScript type definitions
├── utils/               # Utilities
│   └── pdfExport.tsx    # PDF generation
├── contexts/            # React contexts
└── styles/              # Global styles
```

### Tech Stack

- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Three.js & React Three Fiber** - 3D graphics
- **Zustand** - State management
- **React PDF Renderer** - PDF generation
- **Axios** - HTTP client
- **React Dropzone** - File uploads
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running backend API (FastAPI)

### Installation

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Pages & Features

### 1. Upload Page (`/upload`)

**Purpose**: File upload with progress tracking

**Features**:
- Drag-and-drop STEP/STP file upload
- Real-time progress streaming via Server-Sent Events (SSE)
- File validation (size limit: 50 MB)
- Current processing stage display
- Error handling and retry

**Flow**:
1. User drops/selects a STEP file
2. Backend processes file in background
3. Frontend streams progress updates
4. Redirects to viewer when complete

### 2. Viewer Page (`/viewer/[modelId]`)

**Purpose**: 3D model visualization and exploration

**Features**:
- Interactive 3D viewer with orbit controls
- IKEA-style isometric camera positioning
- Real-time model loading from geometry data
- Sidebar with model information
- Actions to extract parts or generate assembly instructions

**Controls**:
- **Left click + drag**: Rotate model
- **Scroll**: Zoom in/out
- **Right click + drag**: Pan view

### 3. Parts Page (`/parts/[modelId]`)

**Purpose**: Display extracted parts with classification

**Features**:
- Grid view of all extracted parts
- Part type classification (panel, hardware, fastener, structural, other)
- Volume and dimensions for each part
- Quantity indicators for identical parts
- Selectable parts with highlighted state
- Navigation to assembly instructions

**Part Information**:
- Unique part ID
- Part type
- Quantity (for grouped identical parts)
- Volume (cm³)
- Dimensions (width, height, depth)

### 4. Assembly Page (`/assembly/[modelId]`)

**Purpose**: Step-by-step assembly instructions

**Features**:
- Multi-step assembly guide
- Previous/Next navigation
- Current step display
- Step-by-step details:
  - Title and description
  - AI-generated detailed instructions
  - Parts involved in this step
  - Assembly sequence
  - Safety tips and warnings
- SVG diagram area (placeholder for exploded view diagrams)
- PDF export of entire manual
- "New Project" button on last step

**Step Components**:
- Assembly sequence (ordered steps)
- Tips and safety warnings
- Confidence score for AI-generated instructions
- Duration estimate

## State Management

### Zustand Store (`app/store/appStore.ts`)

**Processing State**:
- `jobId`: Current job ID
- `modelId`: Current model ID
- `status`: 'idle' | 'uploading' | 'processing' | 'complete' | 'error'
- `progress`: Percentage (0-100)
- `currentStage`: Processing stage name
- `errorMessage`: Error details if any

**Model State**:
- `geometry`: 3D geometry data
- `parts`: Extracted parts list
- `assembly`: Assembly instructions
- `isLoading`: Loading flag
- `error`: Error message

**Example Usage**:
```typescript
const { processing, model, setProgress, setGeometry } = useAppStore();
```

## API Integration

### API Client (`app/services/api.ts`)

Abstraction layer for backend API calls:

```typescript
// Upload STEP file
const response = await apiService.uploadStepFile(file);

// Get model with geometry
const model = await apiService.getModel(modelId);

// Generate parts 2D drawings
const parts = await apiService.generateParts2D(modelId);

// Generate assembly analysis
const assembly = await apiService.generateAssemblyAnalysis(modelId, previewOnly);

// Stream progress via SSE
const eventSource = apiService.streamProgress(jobId);
```

### Progress Streaming

The `useProgress` hook handles Server-Sent Events (SSE) for real-time progress:

```typescript
useProgress(jobId, {
  onProgress: (event) => {
    console.log(`Progress: ${event.progress_percent}%`);
    console.log(`Stage: ${event.current_stage}`);
  },
  onComplete: () => console.log('Done!'),
  onError: (error) => console.error(error),
});
```

## 3D Viewer Implementation

### GeometryViewer Component

Built with React Three Fiber for efficient 3D rendering:

**Features**:
- Automatic camera positioning based on geometry bounds
- IKEA-style isometric view ((-1, -2, 0.5) direction)
- Ambient and directional lighting
- Grid background for scale reference
- Orbit controls for interaction

**Key Functions**:
- `GeometryMesh`: Renders triangulated geometry
- `CameraController`: Positions camera automatically
- `GeometryCanvas`: Sets up Three.js scene

**Geometry Data Format**:
```typescript
interface Geometry {
  vertices: number[][];      // [[x, y, z], ...]
  normals: number[][];       // [[nx, ny, nz], ...]
  indices: number[];         // Triangle indices
  metadata?: Record<string, any>;
}
```

## PDF Export

### AssemblyInstructionsPDF Component

Generated using React PDF Renderer:

**Exports**:
- Cover page with project info
- Parts list page with specifications
- Assembly instruction pages (one per step)
- Each step includes:
  - Step number and title
  - Description and AI-generated details
  - Parts involved
  - Assembly sequence
  - Tips and warnings

**Usage**:
```typescript
<AssemblyInstructionsPDFDownload
  fileName="furniture-assembly"
  parts={parts}
  steps={steps}
/>
```

## Error Handling

Comprehensive error handling across all pages:

- **Upload Errors**: File validation, size limits, format validation
- **Loading Errors**: Network failures, missing data
- **Processing Errors**: Backend failures, timeouts
- **Type Errors**: TypeScript strict mode enabled

**Error Display**:
- User-friendly error messages in Polish
- Error recovery options (retry buttons)
- Detailed error logs in console

## Build & Deployment

### Development

```bash
npm run dev    # Start development server on :3000
```

### Production

```bash
npm run build  # TypeScript check + Next.js build
npm run start  # Run production server
```

### Docker Deployment

```bash
docker build -t weble-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=... weble-frontend
```

## Performance Considerations

- **Code Splitting**: Automatic per-page splitting via Next.js
- **Image Optimization**: Next.js Image component for assets
- **Bundle Size**: Tree shaking, minification in production
- **3D Performance**: WebGL rendering via Three.js
- **State Management**: Zustand for minimal overhead
- **API Caching**: SSE for real-time updates, no polling

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- WebGL required for 3D viewer

## Development Workflow

### Adding a New Page

1. Create folder in `app/[pagename]`
2. Add `page.tsx` component
3. Use Zustand store for state
4. Call API service methods
5. Style with Tailwind CSS

### Adding a Component

1. Create in `app/components/[ComponentName].tsx`
2. Use TypeScript for type safety
3. Keep components focused and reusable
4. Export from component file

### Adding an API Endpoint

1. Add method to `app/services/api.ts`
2. Define TypeScript types in `app/types/index.ts`
3. Use in components with Zustand
4. Handle errors properly

## Testing

```bash
npm run test    # Run tests (if configured)
npm run lint    # Check code quality
```

## Troubleshooting

### API Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Update API URL in .env.local
NEXT_PUBLIC_API_URL=http://your-backend-url/api/v1
```

### 3D Viewer Not Showing

- Check WebGL support in browser
- Verify geometry data is valid
- Check browser console for errors
- Clear cache and reload

### SSE Connection Issues

- Verify backend supports SSE headers (CORS, Cache-Control)
- Check EventSource in browser DevTools Network tab
- Ensure job_id is valid

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -m 'Add my feature'`
3. Push to branch: `git push origin feature/my-feature`
4. Open Pull Request

## License

MIT - See LICENSE file

## Support

For issues and feature requests, please open an issue on GitHub or contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: 2024
