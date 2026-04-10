# WEBLE Pipeline: Implementation Reference

**Companion document to PIPELINE_ARCHITECTURE.md**
**Provides practical code examples and configuration patterns**

---

## Table of Contents
1. [Stage-by-Stage Implementation Details](#stage-by-stage-implementation)
2. [Data Structure Definitions](#data-structures)
3. [Configuration Templates](#configuration)
4. [Testing Strategies](#testing)
5. [Performance Considerations](#performance)

---

## Stage-by-Stage Implementation

### Stage 1: STEP File Loading with CadQuery

#### Complete Example

```python
# backend/app/processors/step_loader.py
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import cadquery as cq
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SolidMetadata:
    """Metadata for a single solid from STEP file."""
    solid_id: str
    face_count: int
    vertex_count: int
    volume: float
    centroid: Tuple[float, float, float]
    bounding_box: Dict[str, Dict[str, float]]

@dataclass
class GeometryData:
    """Complete geometry output from Stage 1."""
    model_id: str
    file_hash: str
    triangulated_mesh: Dict[str, np.ndarray]  # vertices, normals, indices
    bounding_box: Dict[str, Dict[str, float]]
    solids: List[SolidMetadata]
    total_triangles: int

class StepLoaderStage:
    """Loads STEP file and extracts 3D geometry."""
    
    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size_mb = max_file_size_mb
    
    async def process(self, file_path: Path) -> GeometryData:
        """
        Process STEP file asynchronously.
        
        Args:
            file_path: Path to uploaded STEP file
            
        Returns:
            GeometryData with triangulated mesh and metadata
        """
        # Validate file
        self._validate_file(file_path)
        
        # Load in separate thread to avoid blocking
        geometry = await asyncio.to_thread(self._load_step_file, file_path)
        
        return geometry
    
    def _load_step_file(self, file_path: Path) -> GeometryData:
        """Load STEP file using CadQuery (blocks, run in thread)."""
        
        try:
            # Import STEP file
            cad_object = cq.importers.importStep(str(file_path))
            logger.info(f"Loaded STEP file: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to load STEP file: {e}")
            raise
        
        # Extract solids
        solids = cad_object.solids().vals()
        logger.info(f"Found {len(solids)} solids")
        
        # Generate triangulated mesh
        triangulation = self._triangulate_solids(solids)
        
        # Calculate metadata for each solid
        solids_metadata = []
        for i, solid in enumerate(solids):
            metadata = self._extract_solid_metadata(solid, f"solid_{i}")
            solids_metadata.append(metadata)
        
        # Calculate overall bounding box
        bbox = self._calculate_bounding_box(triangulation['vertices'])
        
        # Calculate file hash for caching
        file_hash = self._compute_file_hash(file_path)
        
        return GeometryData(
            model_id=file_hash,  # Use hash as model ID
            file_hash=file_hash,
            triangulated_mesh=triangulation,
            bounding_box=bbox,
            solids=solids_metadata,
            total_triangles=len(triangulation['indices']) // 3
        )
    
    def _triangulate_solids(self, solids: List) -> Dict[str, np.ndarray]:
        """
        Convert solids to triangulated mesh.
        
        Returns:
            {
                'vertices': nx3 array of vertex coordinates,
                'normals': nx3 array of vertex normals,
                'indices': mx3 array of triangle indices
            }
        """
        all_vertices = []
        all_normals = []
        all_indices = []
        vertex_offset = 0
        
        for solid in solids:
            try:
                # Use CadQuery's built-in tessellation
                mesh = solid.toMesh()
                
                # Extract vertex and face data
                vertices = np.array(mesh.Vertices)
                triangles = np.array(mesh.Triangles)
                
                # Calculate normals using cross product
                normals = self._compute_vertex_normals(vertices, triangles)
                
                # Update indices (add offset for multiple solids)
                updated_indices = triangles + vertex_offset
                
                # Accumulate
                all_vertices.append(vertices)
                all_normals.append(normals)
                all_indices.append(updated_indices)
                
                vertex_offset += len(vertices)
                
            except Exception as e:
                logger.warning(f"Failed to triangulate solid: {e}")
                # Continue with other solids
                continue
        
        # Concatenate all
        if not all_vertices:
            raise ValueError("No solids could be triangulated")
        
        return {
            'vertices': np.vstack(all_vertices).astype(np.float32),
            'normals': np.vstack(all_normals).astype(np.float32),
            'indices': np.vstack(all_indices).astype(np.uint32).flatten()
        }
    
    def _compute_vertex_normals(self, vertices: np.ndarray, triangles: np.ndarray) -> np.ndarray:
        """
        Compute smooth vertex normals using face normals.
        
        Algorithm:
        1. Calculate face normal for each triangle
        2. For each vertex, average normals of adjacent faces
        3. Normalize
        """
        normals = np.zeros_like(vertices)
        
        for tri_idx, triangle in enumerate(triangles):
            # Get vertices of this triangle
            v0 = vertices[triangle[0]]
            v1 = vertices[triangle[1]]
            v2 = vertices[triangle[2]]
            
            # Calculate face normal using cross product
            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)
            face_normal = face_normal / (np.linalg.norm(face_normal) + 1e-8)
            
            # Add to each vertex normal
            for vertex_idx in triangle:
                normals[vertex_idx] += face_normal
        
        # Normalize all vertex normals
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / (norms + 1e-8)
        
        return normals
    
    def _extract_solid_metadata(self, solid, solid_id: str) -> SolidMetadata:
        """Extract metadata from a solid."""
        
        # Volume
        volume = float(solid.Volume)
        
        # Centroid
        center = solid.Center
        centroid = (float(center.x), float(center.y), float(center.z))
        
        # Bounding box
        bbox = solid.BoundingBox()
        bounding_box = {
            'min': {'x': float(bbox.xmin), 'y': float(bbox.ymin), 'z': float(bbox.zmin)},
            'max': {'x': float(bbox.xmax), 'y': float(bbox.ymax), 'z': float(bbox.zmax)}
        }
        
        # Face and vertex counts (approximate)
        faces = list(solid.faces())
        face_count = len(faces)
        vertex_count = sum(len(list(face.vertices())) for face in faces)
        
        return SolidMetadata(
            solid_id=solid_id,
            face_count=face_count,
            vertex_count=vertex_count,
            volume=volume,
            centroid=centroid,
            bounding_box=bounding_box
        )
    
    def _calculate_bounding_box(self, vertices: np.ndarray) -> Dict:
        """Calculate overall bounding box from vertices."""
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)
        
        return {
            'min': {'x': float(min_coords[0]), 'y': float(min_coords[1]), 'z': float(min_coords[2])},
            'max': {'x': float(max_coords[0]), 'y': float(max_coords[1]), 'z': float(max_coords[2])}
        }
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file for caching."""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _validate_file(self, file_path: Path):
        """Validate file exists and is within size limit."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File exceeds max size: {file_size_mb}MB > {self.max_file_size_mb}MB")
        
        if file_path.suffix.lower() not in ['.step', '.stp']:
            raise ValueError(f"Invalid file format: {file_path.suffix}")
```

---

### Stage 2: Parts Extraction & Classification

```python
# backend/app/processors/parts_extractor.py
import asyncio
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PartClassification(Enum):
    """Part classification types."""
    PANEL = "panel"
    HARDWARE = "hardware"
    FASTENER = "fastener"
    STRUCTURAL = "structural"
    OTHER = "other"

@dataclass
class PartMetrics:
    """Metrics for part comparison and classification."""
    volume: float
    bounding_box: Dict
    dimensions: Dict[str, float]  # width, height, depth
    aspect_ratios: Dict[str, float]  # ratio of dimensions
    centroid: tuple

@dataclass
class Part:
    """A single part extracted from assembly."""
    part_id: str
    solid_ids: List[str]
    quantity: int
    classification: PartClassification
    metrics: PartMetrics
    deduplication_group: str = None

class PartsExtractorStage:
    """Extracts and classifies parts from geometry."""
    
    def __init__(self, volume_tolerance: float = 0.15, dimension_tolerance: float = 0.15):
        """
        Args:
            volume_tolerance: Tolerance for volume comparison (15%)
            dimension_tolerance: Tolerance for dimension comparison (15%)
        """
        self.volume_tolerance = volume_tolerance
        self.dimension_tolerance = dimension_tolerance
    
    async def process(self, geometry_data: 'GeometryData') -> List[Part]:
        """
        Extract and classify parts from geometry.
        
        Args:
            geometry_data: Output from Stage 1
            
        Returns:
            List of Part objects with classifications
        """
        # Extract individual parts (may split solids if disconnected)
        parts = await asyncio.to_thread(self._extract_parts, geometry_data)
        
        # Classify each part
        parts = await asyncio.to_thread(self._classify_parts, parts)
        
        # Deduplicate similar parts
        parts = await asyncio.to_thread(self._deduplicate_parts, parts)
        
        return parts
    
    def _extract_parts(self, geometry_data: 'GeometryData') -> List[Part]:
        """Extract individual parts from solids."""
        parts = []
        
        for solid_metadata in geometry_data.solids:
            # For now, each solid = one part
            # In future: could split disconnected components
            
            metrics = PartMetrics(
                volume=solid_metadata.volume,
                bounding_box=solid_metadata.bounding_box,
                dimensions=self._calculate_dimensions(solid_metadata.bounding_box),
                aspect_ratios=self._calculate_aspect_ratios(solid_metadata.bounding_box),
                centroid=solid_metadata.centroid
            )
            
            part = Part(
                part_id=f"part_{chr(65 + len(parts))}",  # A, B, C, ...
                solid_ids=[solid_metadata.solid_id],
                quantity=1,
                classification=PartClassification.OTHER,
                metrics=metrics
            )
            
            parts.append(part)
        
        return parts
    
    def _classify_parts(self, parts: List[Part]) -> List[Part]:
        """Classify each part based on geometry."""
        
        for part in parts:
            # Classification logic
            if self._is_panel(part.metrics):
                part.classification = PartClassification.PANEL
            elif self._is_fastener(part.metrics):
                part.classification = PartClassification.FASTENER
            elif self._is_hardware(part.metrics):
                part.classification = PartClassification.HARDWARE
            elif self._is_structural(part.metrics):
                part.classification = PartClassification.STRUCTURAL
            else:
                part.classification = PartClassification.OTHER
        
        return parts
    
    def _deduplicate_parts(self, parts: List[Part]) -> List[Part]:
        """
        Identify and group identical/similar parts.
        
        Algorithm:
        1. Sort by volume
        2. Compare nearby (by volume) parts
        3. Group similar parts, increment quantity
        """
        if len(parts) == 0:
            return parts
        
        # Sort by volume
        parts_sorted = sorted(parts, key=lambda p: p.metrics.volume)
        
        deduplicated = []
        used_indices = set()
        group_counter = 0
        
        for i, part_i in enumerate(parts_sorted):
            if i in used_indices:
                continue
            
            # Start new deduplication group
            group = [part_i]
            used_indices.add(i)
            
            # Find similar parts
            for j in range(i + 1, len(parts_sorted)):
                if j in used_indices:
                    continue
                
                part_j = parts_sorted[j]
                
                # Stop comparing if volume is too different
                if self._volume_ratio(part_i.metrics.volume, part_j.metrics.volume) > (1 + self.volume_tolerance):
                    break
                
                # Check if similar
                if self._are_similar(part_i.metrics, part_j.metrics):
                    group.append(part_j)
                    used_indices.add(j)
            
            # Create consolidated part
            consolidated = self._consolidate_parts(group, group_id=f"group_{group_counter}")
            deduplicated.append(consolidated)
            group_counter += 1
        
        return deduplicated
    
    def _is_panel(self, metrics: PartMetrics) -> bool:
        """Detect if part is a panel (large, very flat)."""
        dims = sorted(metrics.dimensions.values())
        
        # Panel: large area, minimal thickness
        # Check if smallest dimension << largest dimension
        return (dims[0] < 5) and (dims[1] * dims[2] > 1000)
    
    def _is_fastener(self, metrics: PartMetrics) -> bool:
        """Detect if part is a fastener (small, specific geometry)."""
        volume = metrics.volume
        
        # Fasteners are small (< 50mm³) and numerous
        return 1 < volume < 50
    
    def _is_hardware(self, metrics: PartMetrics) -> bool:
        """Detect if part is hardware (cam locks, dowels, etc.)."""
        volume = metrics.volume
        
        # Hardware: small to medium (50-500mm³)
        return 50 < volume < 500
    
    def _is_structural(self, metrics: PartMetrics) -> bool:
        """Detect if part is structural (medium to large, not flat)."""
        volume = metrics.volume
        dims = sorted(metrics.dimensions.values())
        
        # Structural: large volume, relatively balanced dimensions
        is_large = volume > 500
        not_flat = dims[0] > 10  # No very thin dimensions
        not_tiny = dims[1] > 20
        
        return is_large and not_flat and not_tiny
    
    def _are_similar(self, metrics_a: PartMetrics, metrics_b: PartMetrics) -> bool:
        """Check if two parts are similar (within tolerance)."""
        
        # Volume comparison
        volume_ratio = self._volume_ratio(metrics_a.volume, metrics_b.volume)
        if volume_ratio > (1 + self.volume_tolerance):
            return False
        
        # Dimension comparison (sorted to be order-invariant)
        dims_a = sorted(metrics_a.dimensions.values())
        dims_b = sorted(metrics_b.dimensions.values())
        
        for d_a, d_b in zip(dims_a, dims_b):
            ratio = self._dimension_ratio(d_a, d_b)
            if ratio > (1 + self.dimension_tolerance):
                return False
        
        return True
    
    @staticmethod
    def _volume_ratio(v1: float, v2: float) -> float:
        """Calculate ratio of two volumes (always > 1)."""
        ratio = max(v1, v2) / (min(v1, v2) + 1e-6)
        return ratio
    
    @staticmethod
    def _dimension_ratio(d1: float, d2: float) -> float:
        """Calculate ratio of two dimensions (always > 1)."""
        ratio = max(d1, d2) / (min(d1, d2) + 1e-6)
        return ratio
    
    @staticmethod
    def _calculate_dimensions(bounding_box: Dict) -> Dict[str, float]:
        """Calculate width, height, depth from bounding box."""
        min_pt = bounding_box['min']
        max_pt = bounding_box['max']
        
        return {
            'width': abs(max_pt['x'] - min_pt['x']),
            'height': abs(max_pt['y'] - min_pt['y']),
            'depth': abs(max_pt['z'] - min_pt['z'])
        }
    
    @staticmethod
    def _calculate_aspect_ratios(bounding_box: Dict) -> Dict[str, float]:
        """Calculate aspect ratios from bounding box."""
        dims = PartsExtractorStage._calculate_dimensions(bounding_box)
        w, h, d = dims['width'], dims['height'], dims['depth']
        
        return {
            'width_height': w / (h + 1e-6),
            'width_depth': w / (d + 1e-6),
            'height_depth': h / (d + 1e-6)
        }
    
    def _consolidate_parts(self, parts: List[Part], group_id: str) -> Part:
        """Consolidate multiple identical parts into one."""
        consolidated = parts[0]
        consolidated.quantity = len(parts)
        consolidated.deduplication_group = group_id
        consolidated.solid_ids = [p.solid_ids[0] for p in parts]
        
        return consolidated
```

---

## Data Structures

### Complete Type Definitions

```python
# backend/app/models/geometry.py
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np

@dataclass
class RawGeometry:
    """Output from Stage 1: STEP file loading."""
    model_id: str
    file_hash: str
    triangulated_mesh: Dict[str, np.ndarray]
    bounding_box: Dict[str, Dict[str, float]]
    solids: List['SolidMetadata']
    total_triangles: int

# backend/app/models/parts.py
from enum import Enum

class PartClassification(Enum):
    PANEL = "panel"
    HARDWARE = "hardware"
    FASTENER = "fastener"
    STRUCTURAL = "structural"
    OTHER = "other"

@dataclass
class Part:
    """Individual furniture part."""
    part_id: str
    solid_ids: List[str]
    quantity: int
    classification: PartClassification
    metrics: 'PartMetrics'
    deduplication_group: str = None
    svg_drawing: str = None

@dataclass
class PartsList:
    """Output from Stage 2: Parts extraction."""
    model_id: str
    parts: List[Part]
    deduplication_groups: Dict[str, List[str]]

# backend/app/models/assembly.py
@dataclass
class AssemblyStep:
    """Single step in assembly sequence."""
    step_number: int
    title: str
    description: str
    part_indices: List[int]
    part_roles: Dict[int, str]
    context_part_indices: List[int]
    exploded_view_svg: str = None
    estimated_time_minutes: int = None
    difficulty: str = "moderate"  # easy, moderate, hard
    tools: List[str] = None

@dataclass
class AssemblySteps:
    """Output from Stage 4: Assembly instruction generation."""
    model_id: str
    steps: List[AssemblyStep]
    total_estimated_time_minutes: int
    total_steps: int
    difficulty: str
    tools_required: List[str]
```

---

## Configuration

### Environment Variables Template

```bash
# backend/.env

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/weble

# Cache
REDIS_URL=redis://localhost:6379/0

# File Storage
S3_BUCKET=weble-files
S3_ENDPOINT=http://localhost:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# LLM API
OPENROUTER_API_KEY=sk_...
LLM_MODEL=openrouter/google/gemini-pro
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3

# Processing
STEP_LOADER_TIMEOUT_SECONDS=120
PARTS_EXTRACTOR_TIMEOUT_SECONDS=60
DRAWING_GENERATOR_TIMEOUT_SECONDS=180
ASSEMBLY_GENERATOR_TIMEOUT_SECONDS=60

# Geometry parameters
GEOMETRY_VOLUME_TOLERANCE=0.15
GEOMETRY_DIMENSION_TOLERANCE=0.15
TRIANGULATION_QUALITY=medium  # low, medium, high

# Performance
MAX_UPLOAD_SIZE_MB=50
WORKER_THREADS=4
CACHE_TTL_SECONDS=3600

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

### Startup Configuration

```python
# backend/app/core/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment."""
    
    # Database
    database_url: str
    
    # Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600
    
    # File Storage
    s3_bucket: str
    s3_endpoint: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_access_key: str
    s3_secret_key: str
    
    # LLM
    openrouter_api_key: str
    llm_model: str = "openrouter/google/gemini-pro"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 3
    
    # Processing
    step_loader_timeout_seconds: int = 120
    parts_extractor_timeout_seconds: int = 60
    drawing_generator_timeout_seconds: int = 180
    assembly_generator_timeout_seconds: int = 60
    
    # Geometry
    volume_tolerance: float = 0.15
    dimension_tolerance: float = 0.15
    triangulation_quality: str = "medium"
    
    # Performance
    max_upload_size_mb: int = 50
    worker_threads: int = 4
    
    # Logging
    log_level: str = "INFO"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()
```

---

## Testing

### Unit Test Example: Parts Deduplication

```python
# backend/tests/test_parts_extractor.py
import pytest
from app.processors.parts_extractor import PartsExtractorStage, Part, PartClassification, PartMetrics

@pytest.fixture
def extractor():
    return PartsExtractorStage(volume_tolerance=0.15, dimension_tolerance=0.15)

@pytest.fixture
def sample_parts(extractor):
    """Create sample parts for testing."""
    
    metrics_a = PartMetrics(
        volume=100.0,
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 10, 'y': 10, 'z': 1}},
        dimensions={'width': 10, 'height': 10, 'depth': 1},
        aspect_ratios={'width_height': 1.0, 'width_depth': 10.0, 'height_depth': 10.0},
        centroid=(5, 5, 0.5)
    )
    
    part_a = Part(
        part_id="part_A",
        solid_ids=["solid_0"],
        quantity=1,
        classification=PartClassification.PANEL,
        metrics=metrics_a
    )
    
    # Part B: Almost identical to A (within 15% tolerance)
    metrics_b = PartMetrics(
        volume=110.0,  # 10% difference
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 10.5, 'y': 10.5, 'z': 1}},
        dimensions={'width': 10.5, 'height': 10.5, 'depth': 1},
        aspect_ratios={'width_height': 1.0, 'width_depth': 10.5, 'height_depth': 10.5},
        centroid=(5.25, 5.25, 0.5)
    )
    
    part_b = Part(
        part_id="part_B",
        solid_ids=["solid_1"],
        quantity=1,
        classification=PartClassification.PANEL,
        metrics=metrics_b
    )
    
    # Part C: Significantly different (20% difference, outside tolerance)
    metrics_c = PartMetrics(
        volume=125.0,  # 25% difference
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 11.2, 'y': 11.2, 'z': 1}},
        dimensions={'width': 11.2, 'height': 11.2, 'depth': 1},
        aspect_ratios={'width_height': 1.0, 'width_depth': 11.2, 'height_depth': 11.2},
        centroid=(5.6, 5.6, 0.5)
    )
    
    part_c = Part(
        part_id="part_C",
        solid_ids=["solid_2"],
        quantity=1,
        classification=PartClassification.PANEL,
        metrics=metrics_c
    )
    
    return [part_a, part_b, part_c]

def test_deduplication_within_tolerance(extractor, sample_parts):
    """Test that parts within 15% tolerance are grouped."""
    
    result = extractor._deduplicate_parts(sample_parts)
    
    # Part A and B should be grouped, C should be separate
    assert len(result) == 2
    assert result[0].quantity == 2  # A and B grouped
    assert result[1].quantity == 1  # C alone

def test_deduplication_group_consolidation(extractor):
    """Test that grouped parts share solid IDs and quantity."""
    
    metrics = PartMetrics(
        volume=100.0,
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 10, 'y': 10, 'z': 1}},
        dimensions={'width': 10, 'height': 10, 'depth': 1},
        aspect_ratios={},
        centroid=(5, 5, 0.5)
    )
    
    parts = [
        Part("part_A", ["solid_0"], 1, PartClassification.FASTENER, metrics),
        Part("part_B", ["solid_1"], 1, PartClassification.FASTENER, metrics),
        Part("part_C", ["solid_2"], 1, PartClassification.FASTENER, metrics),
    ]
    
    result = extractor._deduplicate_parts(parts)
    
    assert len(result) == 1
    assert result[0].quantity == 3
    assert len(result[0].solid_ids) == 3

def test_classification_detection(extractor):
    """Test part classification logic."""
    
    # Large, flat = panel
    panel_metrics = PartMetrics(
        volume=1000.0,
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 100, 'y': 200, 'z': 2}},
        dimensions={'width': 100, 'height': 200, 'depth': 2},
        aspect_ratios={},
        centroid=(50, 100, 1)
    )
    
    assert extractor._is_panel(panel_metrics) == True
    
    # Small = fastener
    fastener_metrics = PartMetrics(
        volume=10.0,
        bounding_box={'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 5, 'y': 5, 'z': 0.5}},
        dimensions={'width': 5, 'height': 5, 'depth': 0.5},
        aspect_ratios={},
        centroid=(2.5, 2.5, 0.25)
    )
    
    assert extractor._is_fastener(fastener_metrics) == True
```

---

## Performance Considerations

### Benchmarking Example

```python
# backend/app/services/performance_monitor.py
import time
import logging
from contextlib import contextmanager
from typing import Dict

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Track stage execution times for optimization."""
    
    def __init__(self):
        self.timings: Dict[str, list] = {}
    
    @contextmanager
    def measure(self, stage_name: str):
        """Context manager to measure stage execution time."""
        start_time = time.time()
        
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            
            if stage_name not in self.timings:
                self.timings[stage_name] = []
            
            self.timings[stage_name].append(elapsed_ms)
            
            # Log and summarize
            avg_time = sum(self.timings[stage_name]) / len(self.timings[stage_name])
            logger.info(
                f"Stage '{stage_name}': {elapsed_ms:.1f}ms (avg: {avg_time:.1f}ms)"
            )
    
    def get_summary(self) -> Dict:
        """Get performance summary."""
        return {
            stage_name: {
                'min': min(times),
                'max': max(times),
                'avg': sum(times) / len(times),
                'total': sum(times)
            }
            for stage_name, times in self.timings.items()
        }

# Usage example
monitor = PerformanceMonitor()

async def process_pipeline(geometry_data):
    with monitor.measure("step_loading"):
        # ... Step 1 code
        pass
    
    with monitor.measure("parts_extraction"):
        # ... Step 2 code
        pass
    
    print(monitor.get_summary())
```

### Memory Optimization

```python
# For large assemblies (>100k parts)

class StreamingPartsExtractor:
    """Extract and process parts in streams to minimize memory."""
    
    async def process_streaming(self, geometry_data, batch_size=1000):
        """
        Process parts in batches to avoid loading all into memory.
        
        Good for: 10k-100k parts
        """
        
        all_solids = geometry_data.solids
        
        for batch_start in range(0, len(all_solids), batch_size):
            batch_end = min(batch_start + batch_size, len(all_solids))
            batch = all_solids[batch_start:batch_end]
            
            # Process batch
            batch_parts = self._process_batch(batch)
            
            # Yield to caller (generator pattern)
            yield batch_parts
            
            # Memory is freed after each batch
```

---

**End of Implementation Reference**
