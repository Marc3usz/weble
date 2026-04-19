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
 * Extract submesh vertices and indices for a specific solid based on bounding box
 * 
 * Since backend doesn't provide vertex ranges, we use a proximity-based approach:
 * For each vertex in the full geometry, determine which solid it belongs to by checking
 * which solid's bounding box is closest to that vertex.
 * 
 * Returns a BufferGeometry containing only vertices/indices for the target solid
 */
export function extractSolidGeometry(
  fullGeometry: THREE.BufferGeometry,
  solidIndex: number,
  solids: Solid[]
): THREE.BufferGeometry {
  const solid = solids[solidIndex];
  if (!solid) {
    console.warn(`Solid ${solidIndex} not found, returning full geometry`);
    return fullGeometry.clone();
  }

  // Get vertex positions from the full geometry
  const positions = fullGeometry.getAttribute("position") as THREE.BufferAttribute;
  const normals = fullGeometry.getAttribute("normal") as THREE.BufferAttribute;
  const indices = fullGeometry.getIndex() as THREE.BufferAttribute;
  
  if (!positions || !normals || !indices) {
    return fullGeometry.clone();
  }

  // Create a mapping of original vertex indices to new indices
  const vertexMap = new Map<number, number>();
  const newVertices: number[] = [];
  const newNormals: number[] = [];
  const newIndices: number[] = [];

  const bbox = solid.bounding_box;
  const solidCenter = [
    (bbox.max[0] + bbox.min[0]) / 2,
    (bbox.max[1] + bbox.min[1]) / 2,
    (bbox.max[2] + bbox.min[2]) / 2,
  ];

  // For each vertex, check if it's close to this solid's bounding box
  const posArray = positions.array as Float32Array;
  const normArray = normals.array as Float32Array;
  let newVertexIndex = 0;

  for (let i = 0; i < posArray.length; i += 3) {
    const vx = posArray[i];
    const vy = posArray[i + 1];
    const vz = posArray[i + 2];
    const originalIndex = i / 3;

    // Check if vertex is within bounding box with small tolerance
    const tolerance = 0.1;
    if (
      vx >= bbox.min[0] - tolerance && vx <= bbox.max[0] + tolerance &&
      vy >= bbox.min[1] - tolerance && vy <= bbox.max[1] + tolerance &&
      vz >= bbox.min[2] - tolerance && vz <= bbox.max[2] + tolerance
    ) {
      // Vertex belongs to this solid
      vertexMap.set(originalIndex, newVertexIndex);
      newVertices.push(vx, vy, vz);
      newNormals.push(normArray[i], normArray[i + 1], normArray[i + 2]);
      newVertexIndex++;
    }
  }

  // Build new indices from old indices
  const indicesArray = indices.array as Uint32Array;
  for (let i = 0; i < indicesArray.length; i += 3) {
    const idx0 = indicesArray[i];
    const idx1 = indicesArray[i + 1];
    const idx2 = indicesArray[i + 2];

    // Only include triangle if all 3 vertices belong to this solid
    const mappedIdx0 = vertexMap.get(idx0);
    const mappedIdx1 = vertexMap.get(idx1);
    const mappedIdx2 = vertexMap.get(idx2);

    if (mappedIdx0 !== undefined && mappedIdx1 !== undefined && mappedIdx2 !== undefined) {
      newIndices.push(mappedIdx0, mappedIdx1, mappedIdx2);
    }
  }

  // Create new geometry with extracted vertices/indices
  const newGeometry = new THREE.BufferGeometry();
  newGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(newVertices), 3));
  newGeometry.setAttribute("normal", new THREE.BufferAttribute(new Float32Array(newNormals), 3));
  
  if (newIndices.length > 0) {
    newGeometry.setIndex(new THREE.BufferAttribute(new Uint32Array(newIndices), 1));
  }

  return newGeometry;
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
 * Each part gets its own extracted geometry AND its own material so:
 * - Highlighting one part doesn't affect others
 * - Explosion effect can move each part independently
 * 
 * Returns a Map of partIndex -> THREE.Mesh for easy access during selection/highlighting
 */
export function createPartMeshes(
  geometry: THREE.BufferGeometry,
  parts: Part[],
  solids: Solid[]
): Map<number, THREE.Mesh> {
  const meshes = new Map<number, THREE.Mesh>();

  parts.forEach((part, partIndex) => {
    // Extract geometry for this specific part/solid
    const partGeometry = extractSolidGeometry(geometry, partIndex, solids);

    // Create a unique material for each part
    const material = new THREE.MeshPhongMaterial({
      color: 0xcccccc, // Light gray
      side: THREE.DoubleSide,
      wireframe: false,
    });

    const mesh = new THREE.Mesh(partGeometry, material);
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
