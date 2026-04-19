import * as THREE from "three";
import { Part, Solid } from "@/types";

/**
 * Spatially match parts to solids using bounding box comparison
 * 
 * Algorithm:
 * 1. For each part, find the solid with the closest bounding box center
 * 2. Verify that the bounding box dimensions are similar (within tolerance)
 * 3. Return a map of part index to solid index
 * 
 * TODO: Add tolerance tuning parameter if spatial matching is unreliable
 * TODO: Handle edge case where parts outnumber solids or vice versa
 */
export function spatialMatchPartsToBoundingBoxes(
  parts: Part[],
  solids: Solid[]
): Map<number, number> {
  const map = new Map<number, number>();

  parts.forEach((part, partIndex) => {
    let bestMatch = 0;
    let bestDistance = Infinity;

    // Find solid with closest bounding box center
    solids.forEach((solid, solidIndex) => {
      const partBbox = part.dimensions;
      if (!partBbox) {
        // Fallback: match by order if no dimensions
        if (partIndex < solids.length) {
          map.set(partIndex, partIndex);
        }
        return;
      }

      const solidBbox = solid.bounding_box;
      const partCenter = [
        (partBbox.width + partBbox.depth) / 2,
        partBbox.height / 2,
        (partBbox.width + partBbox.depth) / 2,
      ];

      const solidCenter = [
        (solidBbox.max[0] + solidBbox.min[0]) / 2,
        (solidBbox.max[1] + solidBbox.min[1]) / 2,
        (solidBbox.max[2] + solidBbox.min[2]) / 2,
      ];

      const distance = Math.sqrt(
        Math.pow(partCenter[0] - solidCenter[0], 2) +
          Math.pow(partCenter[1] - solidCenter[1], 2) +
          Math.pow(partCenter[2] - solidCenter[2], 2)
      );

      if (distance < bestDistance) {
        bestDistance = distance;
        bestMatch = solidIndex;
      }
    });

    map.set(partIndex, bestMatch);
  });

  return map;
}

/**
 * Create a THREE.BufferGeometry from raw vertices, normals, and indices
 * 
 * TODO: Add geometry optimization (merging nearby vertices, removing duplicates)
 * TODO: Add normal recalculation if backend provides incorrect normals
 */
export function createBufferGeometry(
  vertices: number[][],
  normals: number[][],
  indices: number[]
): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();

  // Flatten arrays for THREE.js BufferGeometry
  const flatVertices = new Float32Array(vertices.flat());
  const flatNormals = new Float32Array(normals.flat());
  const flatIndices = new Uint32Array(indices);

  geometry.setAttribute("position", new THREE.BufferAttribute(flatVertices, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(flatNormals, 3));
  geometry.setIndex(new THREE.BufferAttribute(flatIndices, 1));

  return geometry;
}

/**
 * Extract a submesh from full geometry for a specific solid
 * 
 * NOTE: Backend doesn't provide vertex ranges per solid, so for MVP we render
 * the full geometry. This function is a placeholder for future implementation.
 * 
 * TODO: Implement vertex range extraction when backend provides per-solid vertex data
 * TODO: Create cached submesh system to avoid re-creating same meshes
 */
export function extractSolidGeometry(
  fullGeometry: THREE.BufferGeometry,
  solidIndex: number
): THREE.BufferGeometry {
  // PLACEHOLDER: For MVP, return full geometry
  // In production, we would extract only the vertices/indices for this solid
  return fullGeometry.clone();
}

/**
 * Create a mesh for a part with basic gray material
 * 
 * TODO: Add material variants (normal, highlighted, exploded)
 * TODO: Add material caching to reuse materials across meshes
 */
export function createPartMesh(
  geometry: THREE.BufferGeometry,
  partIndex: number
): THREE.Mesh {
  const material = new THREE.MeshPhongMaterial({
    color: 0xcccccc, // Light gray
    side: THREE.DoubleSide,
    wireframe: false,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData = { partIndex };

  return mesh;
}

/**
 * Create all meshes for parts from full geometry
 * 
 * Returns a Map of partIndex -> THREE.Mesh for easy access during selection/highlighting
 * 
 * Optimization: Share geometry and material across all part meshes (saves memory)
 * 
 * TODO: Implement vertex range extraction to create per-part geometry
 * TODO: Add mesh optimization (LOD system)
 * TODO: Add frustum culling for performance with many parts
 */
export function createPartMeshes(
  geometry: THREE.BufferGeometry,
  parts: Part[]
): Map<number, THREE.Mesh> {
  const meshes = new Map<number, THREE.Mesh>();

  // Reuse material across all parts (saves memory)
  const material = new THREE.MeshPhongMaterial({
    color: 0xcccccc, // Light gray
    side: THREE.DoubleSide,
    wireframe: false,
  });

  parts.forEach((part, partIndex) => {
    // Reuse the same geometry (no cloning - more efficient)
    // In production, we would use extracted submesh geometry for each part
    const mesh = new THREE.Mesh(geometry, material);
    mesh.userData = { partIndex };
    meshes.set(partIndex, mesh);
  });

  return meshes;
}

/**
 * Calculate exploded positions for parts (spreads outward from center)
 * 
 * Returns new positions for each mesh to create exploded view animation
 * 
 * TODO: Implement actual calculation based on bounding box centers
 * TODO: Add configurable explosion distance/direction
 */
export function calculateExplodePositions(
  meshes: Map<number, THREE.Mesh>,
  explosionDistance: number = 2
): Map<number, THREE.Vector3> {
  const positions = new Map<number, THREE.Vector3>();

  meshes.forEach((mesh, partIndex) => {
    // Get bounding box center
    const bbox = new THREE.Box3().setFromObject(mesh);
    const center = bbox.getCenter(new THREE.Vector3());

    // Explosion direction: push away from origin
    const explosionDirection = center.normalize();
    const explosionAmount = explosionDirection.multiplyScalar(explosionDistance);

    positions.set(partIndex, explosionAmount);
  });

  return positions;
}

/**
 * Setup basic Three.js scene with lighting
 * 
 * TODO: Add configurable lighting (intensity, color, position)
 * TODO: Add environment map for better reflections
 * TODO: Add shadow support for more realistic rendering
 */
export function setupScene(): {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  canvas: HTMLCanvasElement;
} {
  const canvas = document.createElement("canvas");
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xfafaf8); // Light background

  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10000);
  camera.position.z = 5;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);

  // Add lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(5, 5, 5);
  scene.add(directionalLight);

  return { scene, camera, renderer, canvas };
}
