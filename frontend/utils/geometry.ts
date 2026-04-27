import * as THREE from "three";
import { Part, Solid } from "@/types";

const DIMENSION_TOLERANCE = 0.12;

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

  if (solids.length === 0) {
    return map;
  }

  // Backend ordering is the most reliable signal currently available.
  // Previous spatial matching produced invalid duplicates because part payload
  // does not include world-space centers.
  parts.forEach((_, partIndex) => {
    map.set(partIndex, Math.min(partIndex, solids.length - 1));
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

  // Recompute normals from topology to avoid broken shading from source normals.
  geometry.computeVertexNormals();
  geometry.normalizeNormals();

  return geometry;
}

/**
 * Extract a submesh from full geometry for a specific solid
 * 
 * NOTE: Backend doesn't provide vertex ranges per solid, so we use a simple approach:
 * Return the full geometry which is shared across all part meshes.
 * Individual materials handle the highlighting (one material per part).
 * 
 * TODO: Implement actual vertex range extraction when backend provides per-solid vertex data
 */
export function extractSolidGeometry(
  fullGeometry: THREE.BufferGeometry,
  solidIndex: number,
  solids: Solid[]
): THREE.BufferGeometry {
  const solid = solids[solidIndex];
  if (!solid) {
    return new THREE.BufferGeometry();
  }

  if (
    solid.index_start !== undefined &&
    solid.index_count !== undefined &&
    solid.vertex_start !== undefined &&
    solid.vertex_count !== undefined
  ) {
    return extractSolidGeometryByRanges(fullGeometry, solid);
  }

  const positionAttr = fullGeometry.getAttribute("position") as THREE.BufferAttribute | null;
  const normalAttr = fullGeometry.getAttribute("normal") as THREE.BufferAttribute | null;
  const indexAttr = fullGeometry.getIndex();

  if (!positionAttr) {
    return new THREE.BufferGeometry();
  }

  const hasIndex = indexAttr !== null;
  const triangleCount = hasIndex
    ? Math.floor(indexAttr.count / 3)
    : Math.floor(positionAttr.count / 3);

  const [minX, minY, minZ] = solid.bounding_box.min;
  const [maxX, maxY, maxZ] = solid.bounding_box.max;
  const tolerance = 1e-4;

  const inBounds = (x: number, y: number, z: number) => {
    return (
      x >= minX - tolerance &&
      x <= maxX + tolerance &&
      y >= minY - tolerance &&
      y <= maxY + tolerance &&
      z >= minZ - tolerance &&
      z <= maxZ + tolerance
    );
  };

  const outPositions: number[] = [];
  const outNormals: number[] = [];
  const outIndices: number[] = [];
  const vertexMap = new Map<number, number>();

  for (let tri = 0; tri < triangleCount; tri++) {
    const i0 = hasIndex ? indexAttr.getX(tri * 3) : tri * 3;
    const i1 = hasIndex ? indexAttr.getX(tri * 3 + 1) : tri * 3 + 1;
    const i2 = hasIndex ? indexAttr.getX(tri * 3 + 2) : tri * 3 + 2;

    const v0x = positionAttr.getX(i0);
    const v0y = positionAttr.getY(i0);
    const v0z = positionAttr.getZ(i0);
    const v1x = positionAttr.getX(i1);
    const v1y = positionAttr.getY(i1);
    const v1z = positionAttr.getZ(i1);
    const v2x = positionAttr.getX(i2);
    const v2y = positionAttr.getY(i2);
    const v2z = positionAttr.getZ(i2);

    const cX = (v0x + v1x + v2x) / 3;
    const cY = (v0y + v1y + v2y) / 3;
    const cZ = (v0z + v1z + v2z) / 3;

    const v0In = inBounds(v0x, v0y, v0z);
    const v1In = inBounds(v1x, v1y, v1z);
    const v2In = inBounds(v2x, v2y, v2z);
    const cIn = inBounds(cX, cY, cZ);

    if (!v0In && !v1In && !v2In && !cIn) {
      continue;
    }

    const sourceIndices = [i0, i1, i2];

    for (let j = 0; j < sourceIndices.length; j++) {
      const sourceIndex = sourceIndices[j];
      let mapped = vertexMap.get(sourceIndex);

      if (mapped === undefined) {
        mapped = outPositions.length / 3;
        vertexMap.set(sourceIndex, mapped);

        outPositions.push(
          positionAttr.getX(sourceIndex),
          positionAttr.getY(sourceIndex),
          positionAttr.getZ(sourceIndex)
        );

        if (normalAttr) {
          outNormals.push(
            normalAttr.getX(sourceIndex),
            normalAttr.getY(sourceIndex),
            normalAttr.getZ(sourceIndex)
          );
        }
      }

      outIndices.push(mapped);
    }
  }

  if (outIndices.length === 0) {
    return new THREE.BufferGeometry();
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(outPositions, 3));

  if (normalAttr && outNormals.length === outPositions.length) {
    geometry.setAttribute("normal", new THREE.Float32BufferAttribute(outNormals, 3));
  }

  geometry.setIndex(outIndices);
  geometry.computeVertexNormals();
  geometry.normalizeNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();

  return geometry;
}

function extractSolidGeometryByRanges(
  fullGeometry: THREE.BufferGeometry,
  solid: Solid
): THREE.BufferGeometry {
  const positionAttr = fullGeometry.getAttribute("position") as THREE.BufferAttribute | null;
  const normalAttr = fullGeometry.getAttribute("normal") as THREE.BufferAttribute | null;
  const indexAttr = fullGeometry.getIndex();

  if (!positionAttr || !indexAttr) {
    return new THREE.BufferGeometry();
  }

  const vertexStart = Math.max(0, solid.vertex_start ?? 0);
  const vertexCount = Math.max(0, solid.vertex_count ?? 0);
  const indexStart = Math.max(0, solid.index_start ?? 0);
  const indexCount = Math.max(0, solid.index_count ?? 0);

  if (vertexCount === 0 || indexCount < 3) {
    return new THREE.BufferGeometry();
  }

  const vertexEnd = Math.min(positionAttr.count, vertexStart + vertexCount);
  const indexEnd = Math.min(indexAttr.count, indexStart + indexCount);

  if (vertexEnd <= vertexStart || indexEnd <= indexStart) {
    return new THREE.BufferGeometry();
  }

  const positions: number[] = [];
  const normals: number[] = [];
  const indices: number[] = [];

  for (let i = vertexStart; i < vertexEnd; i++) {
    positions.push(positionAttr.getX(i), positionAttr.getY(i), positionAttr.getZ(i));
    if (normalAttr) {
      normals.push(normalAttr.getX(i), normalAttr.getY(i), normalAttr.getZ(i));
    }
  }

  for (let i = indexStart; i < indexEnd; i++) {
    const idx = indexAttr.getX(i) - vertexStart;
    if (idx >= 0 && idx < vertexCount) {
      indices.push(idx);
    }
  }

  if (indices.length < 3) {
    return new THREE.BufferGeometry();
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (normalAttr && normals.length === positions.length) {
    geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  }
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  geometry.normalizeNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
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
  solids: Solid[],
  partToSolidMap?: Map<number, number> | null
): Map<number, THREE.Mesh> {
  const meshes = new Map<number, THREE.Mesh>();
  const componentGeometries = buildConnectedComponentGeometries(geometry);
  const solidGeometries = buildSolidGeometries(geometry, solids);

  const sourceGeometries = componentGeometries.length > 1
    ? componentGeometries
    : Array.from(solidGeometries.values());

  const safeSources = sourceGeometries.length > 0
    ? sourceGeometries
    : [geometry.clone()];

  parts.forEach((_, partIndex) => {
    const sourceIndex = partIndex % safeSources.length;
    const partGeometry = safeSources[sourceIndex].clone();

    // Create a unique material for each part
    const material = new THREE.MeshPhongMaterial({
      color: 0xcccccc, // Light gray
      side: THREE.DoubleSide,
      wireframe: false,
    });

    const mesh = new THREE.Mesh(partGeometry, material);
    mesh.userData = { partIndex };

    const positionAttr = partGeometry.getAttribute("position") as THREE.BufferAttribute | undefined;
    if (positionAttr && positionAttr.count > 0) {
      const bbox = new THREE.Box3().setFromBufferAttribute(positionAttr);
      const center = bbox.getCenter(new THREE.Vector3());
      mesh.userData.localCenter = center;
    }

    meshes.set(partIndex, mesh);
  });

  return meshes;
}

export function splitGeometryIntoComponents(
  geometry: THREE.BufferGeometry
): THREE.BufferGeometry[] {
  return buildConnectedComponentGeometries(geometry);
}

export function mapPartsToSolidIndices(
  parts: Part[],
  solids: Solid[]
): Map<number, number[]> {
  const result = new Map<number, number[]>();
  if (parts.length === 0 || solids.length === 0) {
    return result;
  }

  const unassigned = new Set<number>(solids.map((_, i) => i));

  const getSolidDimensions = (solid: Solid) => {
    const bbox = solid.bounding_box;
    const dims = [
      Math.abs(bbox.max[0] - bbox.min[0]),
      Math.abs(bbox.max[1] - bbox.min[1]),
      Math.abs(bbox.max[2] - bbox.min[2]),
    ].sort((a, b) => a - b);
    return dims;
  };

  const getPartDimensions = (part: Part) => {
    if (!part.dimensions) return null;
    const dims = [part.dimensions.width, part.dimensions.height, part.dimensions.depth].sort(
      (a, b) => a - b
    );
    return dims;
  };

  const dimsMatch = (a: number[], b: number[]) => {
    for (let i = 0; i < 3; i++) {
      const denom = Math.max(Math.min(Math.abs(a[i]), Math.abs(b[i])), 1e-6);
      const ratio = Math.max(Math.abs(a[i]), Math.abs(b[i])) / denom;
      if (ratio > 1 + DIMENSION_TOLERANCE) {
        return false;
      }
    }
    return true;
  };

  const solidDims = solids.map(getSolidDimensions);

  parts.forEach((part, partIndex) => {
    const expectedCount = Math.max(1, part.quantity || 1);
    const dims = getPartDimensions(part);
    const matches: number[] = [];

    if (dims) {
      for (let s = 0; s < solids.length; s++) {
        if (dimsMatch(dims, solidDims[s])) {
          matches.push(s);
        }
      }
    }

    const preferred = matches.filter((s) => unassigned.has(s));
    const chosen = preferred.length > 0 ? preferred : matches;
    const selected = chosen.slice(0, expectedCount);

    if (selected.length === 0) {
      const fallback = Array.from(unassigned)[0] ?? (partIndex % solids.length);
      selected.push(fallback);
    }

    selected.forEach((s) => {
      unassigned.delete(s);
    });
    result.set(partIndex, selected);
  });

  return result;
}

export function createSolidMeshes(
  geometry: THREE.BufferGeometry,
  solids: Solid[]
): Map<number, THREE.Mesh> {
  const meshes = new Map<number, THREE.Mesh>();
  const components = buildConnectedComponentGeometries(geometry);
  const usedComponents = new Set<number>();

  const componentSizes = components.map((component) => {
    component.computeBoundingBox();
    const bbox = component.boundingBox;
    const size = bbox ? bbox.getSize(new THREE.Vector3()) : new THREE.Vector3(0, 0, 0);
    return [size.x, size.y, size.z].sort((a, b) => a - b);
  });

  const ratioScore = (a: number[], b: number[]) => {
    let score = 0;
    for (let i = 0; i < 3; i++) {
      const lo = Math.max(Math.min(Math.abs(a[i]), Math.abs(b[i])), 1e-6);
      const hi = Math.max(Math.abs(a[i]), Math.abs(b[i]));
      score += hi / lo;
    }
    return score / 3;
  };

  solids.forEach((solid, solidIndex) => {
    let solidGeometry = extractSolidGeometry(geometry, solidIndex, solids);

    const isRenderable =
      (solidGeometry.getAttribute("position") as THREE.BufferAttribute | null)?.count &&
      (solidGeometry.getIndex()?.count ?? 0) >= 3;

    if (!isRenderable && components.length > 0) {
      const solidDims = [
        Math.abs(solid.bounding_box.max[0] - solid.bounding_box.min[0]),
        Math.abs(solid.bounding_box.max[1] - solid.bounding_box.min[1]),
        Math.abs(solid.bounding_box.max[2] - solid.bounding_box.min[2]),
      ].sort((a, b) => a - b);

      let bestComponent = -1;
      let bestScore = Number.POSITIVE_INFINITY;

      componentSizes.forEach((componentDims, componentIndex) => {
        if (usedComponents.has(componentIndex)) {
          return;
        }
        const score = ratioScore(solidDims, componentDims);
        if (score < bestScore) {
          bestScore = score;
          bestComponent = componentIndex;
        }
      });

      if (bestComponent >= 0 && bestScore < 1.35) {
        solidGeometry = components[bestComponent].clone();
        usedComponents.add(bestComponent);
      }
    }

    const validGeometry =
      ((solidGeometry.getAttribute("position") as THREE.BufferAttribute | null)?.count ?? 0) > 0 &&
      (solidGeometry.getIndex()?.count ?? 0) >= 3;

    if (!validGeometry) {
      solidGeometry.dispose();
      solidGeometry = buildBoundingBoxFallbackGeometry(solid);
    }

    const material = new THREE.MeshPhongMaterial({
      color: 0xa7a2a9,
      side: THREE.DoubleSide,
      wireframe: false,
    });

    const mesh = new THREE.Mesh(solidGeometry, material);
    mesh.userData = { solidIndex };

    const positionAttr = solidGeometry.getAttribute("position") as THREE.BufferAttribute | undefined;
    if (positionAttr && positionAttr.count > 0) {
      const box = new THREE.Box3().setFromBufferAttribute(positionAttr);
      mesh.userData.localCenter = box.getCenter(new THREE.Vector3());
    }

    meshes.set(solidIndex, mesh);
  });

  return meshes;
}

function buildBoundingBoxFallbackGeometry(solid: Solid): THREE.BufferGeometry {
  const geometry = new THREE.BoxGeometry(
    Math.max(Math.abs(solid.bounding_box.max[0] - solid.bounding_box.min[0]), 0.001),
    Math.max(Math.abs(solid.bounding_box.max[1] - solid.bounding_box.min[1]), 0.001),
    Math.max(Math.abs(solid.bounding_box.max[2] - solid.bounding_box.min[2]), 0.001)
  );

  const center = new THREE.Vector3(
    (solid.bounding_box.min[0] + solid.bounding_box.max[0]) / 2,
    (solid.bounding_box.min[1] + solid.bounding_box.max[1]) / 2,
    (solid.bounding_box.min[2] + solid.bounding_box.max[2]) / 2
  );
  geometry.translate(center.x, center.y, center.z);
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

function buildConnectedComponentGeometries(
  geometry: THREE.BufferGeometry
): THREE.BufferGeometry[] {
  const out: THREE.BufferGeometry[] = [];
  const positionAttr = geometry.getAttribute("position") as THREE.BufferAttribute | null;
  const normalAttr = geometry.getAttribute("normal") as THREE.BufferAttribute | null;
  const indexAttr = geometry.getIndex();

  if (!positionAttr || !indexAttr) {
    return out;
  }

  const triangleCount = Math.floor(indexAttr.count / 3);
  if (triangleCount === 0) {
    return out;
  }

  const vertexToTriangles = new Map<number, number[]>();
  const triangleVertices: Array<[number, number, number]> = [];

  for (let tri = 0; tri < triangleCount; tri++) {
    const i0 = indexAttr.getX(tri * 3);
    const i1 = indexAttr.getX(tri * 3 + 1);
    const i2 = indexAttr.getX(tri * 3 + 2);
    triangleVertices.push([i0, i1, i2]);

    [i0, i1, i2].forEach((vertexIndex) => {
      const list = vertexToTriangles.get(vertexIndex) ?? [];
      list.push(tri);
      vertexToTriangles.set(vertexIndex, list);
    });
  }

  const visited = new Array<boolean>(triangleCount).fill(false);

  for (let start = 0; start < triangleCount; start++) {
    if (visited[start]) continue;

    const queue: number[] = [start];
    visited[start] = true;
    const trianglesInComponent: number[] = [];

    while (queue.length > 0) {
      const tri = queue.shift() as number;
      trianglesInComponent.push(tri);

      const [i0, i1, i2] = triangleVertices[tri];
      const neighbors = [
        ...(vertexToTriangles.get(i0) ?? []),
        ...(vertexToTriangles.get(i1) ?? []),
        ...(vertexToTriangles.get(i2) ?? []),
      ];

      neighbors.forEach((neighborTri) => {
        if (!visited[neighborTri]) {
          visited[neighborTri] = true;
          queue.push(neighborTri);
        }
      });
    }

    const positions: number[] = [];
    const normals: number[] = [];
    const indices: number[] = [];
    const vertexMap = new Map<number, number>();

    trianglesInComponent.forEach((tri) => {
      const [i0, i1, i2] = triangleVertices[tri];
      [i0, i1, i2].forEach((sourceIndex) => {
        let mappedIndex = vertexMap.get(sourceIndex);
        if (mappedIndex === undefined) {
          mappedIndex = positions.length / 3;
          vertexMap.set(sourceIndex, mappedIndex);
          positions.push(
            positionAttr.getX(sourceIndex),
            positionAttr.getY(sourceIndex),
            positionAttr.getZ(sourceIndex)
          );
          if (normalAttr) {
            normals.push(
              normalAttr.getX(sourceIndex),
              normalAttr.getY(sourceIndex),
              normalAttr.getZ(sourceIndex)
            );
          }
        }
        indices.push(mappedIndex);
      });
    });

    const componentGeometry = new THREE.BufferGeometry();
    componentGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3)
    );
    if (normalAttr && normals.length === positions.length) {
      componentGeometry.setAttribute(
        "normal",
        new THREE.Float32BufferAttribute(normals, 3)
      );
    } else {
      componentGeometry.computeVertexNormals();
    }
    componentGeometry.setIndex(indices);
    componentGeometry.computeBoundingBox();
    componentGeometry.computeBoundingSphere();
    out.push(componentGeometry);
  }

  out.sort((a, b) => {
    const aCount = (a.getIndex()?.count ?? 0);
    const bCount = (b.getIndex()?.count ?? 0);
    return bCount - aCount;
  });

  return out;
}

function buildSolidGeometries(
  geometry: THREE.BufferGeometry,
  solids: Solid[]
): Map<number, THREE.BufferGeometry> {
  const out = new Map<number, THREE.BufferGeometry>();
  if (solids.length === 0) {
    return out;
  }

  const positionAttr = geometry.getAttribute("position") as THREE.BufferAttribute | null;
  const normalAttr = geometry.getAttribute("normal") as THREE.BufferAttribute | null;
  const indexAttr = geometry.getIndex();

  if (!positionAttr) {
    return out;
  }

  const hasIndex = indexAttr !== null;
  const triangleCount = hasIndex
    ? Math.floor(indexAttr.count / 3)
    : Math.floor(positionAttr.count / 3);

  const tolerance = 1e-4;

  const geometryBounds = new THREE.Box3().setFromBufferAttribute(positionAttr);
  const geometryMin = geometryBounds.min;
  const geometrySize = geometryBounds.getSize(new THREE.Vector3());

  const solidsBounds = solids.reduce(
    (acc, solid) => {
      acc.min.x = Math.min(acc.min.x, solid.bounding_box.min[0]);
      acc.min.y = Math.min(acc.min.y, solid.bounding_box.min[1]);
      acc.min.z = Math.min(acc.min.z, solid.bounding_box.min[2]);
      acc.max.x = Math.max(acc.max.x, solid.bounding_box.max[0]);
      acc.max.y = Math.max(acc.max.y, solid.bounding_box.max[1]);
      acc.max.z = Math.max(acc.max.z, solid.bounding_box.max[2]);
      return acc;
    },
    {
      min: new THREE.Vector3(Number.POSITIVE_INFINITY, Number.POSITIVE_INFINITY, Number.POSITIVE_INFINITY),
      max: new THREE.Vector3(Number.NEGATIVE_INFINITY, Number.NEGATIVE_INFINITY, Number.NEGATIVE_INFINITY),
    }
  );
  const solidsSize = solidsBounds.max.clone().sub(solidsBounds.min);

  const norm = (value: number, min: number, size: number) =>
    (value - min) / (Math.abs(size) < 1e-9 ? 1 : size);

  const normalizedSolidBounds = solids.map((solid) => ({
    min: [
      norm(solid.bounding_box.min[0], solidsBounds.min.x, solidsSize.x),
      norm(solid.bounding_box.min[1], solidsBounds.min.y, solidsSize.y),
      norm(solid.bounding_box.min[2], solidsBounds.min.z, solidsSize.z),
    ] as [number, number, number],
    max: [
      norm(solid.bounding_box.max[0], solidsBounds.min.x, solidsSize.x),
      norm(solid.bounding_box.max[1], solidsBounds.min.y, solidsSize.y),
      norm(solid.bounding_box.max[2], solidsBounds.min.z, solidsSize.z),
    ] as [number, number, number],
  }));

  const solidCenters = normalizedSolidBounds.map((solid) => [
    (solid.min[0] + solid.max[0]) / 2,
    (solid.min[1] + solid.max[1]) / 2,
    (solid.min[2] + solid.max[2]) / 2,
  ]);

  const builders = solids.map(() => ({
    positions: [] as number[],
    normals: [] as number[],
    indices: [] as number[],
    vertexMap: new Map<number, number>(),
  }));

  const centroid = [0, 0, 0];
  const score = new Array<number>(solids.length).fill(0);

  for (let tri = 0; tri < triangleCount; tri++) {
    const i0 = hasIndex ? indexAttr.getX(tri * 3) : tri * 3;
    const i1 = hasIndex ? indexAttr.getX(tri * 3 + 1) : tri * 3 + 1;
    const i2 = hasIndex ? indexAttr.getX(tri * 3 + 2) : tri * 3 + 2;

    const v0x = positionAttr.getX(i0);
    const v0y = positionAttr.getY(i0);
    const v0z = positionAttr.getZ(i0);
    const v1x = positionAttr.getX(i1);
    const v1y = positionAttr.getY(i1);
    const v1z = positionAttr.getZ(i1);
    const v2x = positionAttr.getX(i2);
    const v2y = positionAttr.getY(i2);
    const v2z = positionAttr.getZ(i2);

    centroid[0] = (v0x + v1x + v2x) / 3;
    centroid[1] = (v0y + v1y + v2y) / 3;
    centroid[2] = (v0z + v1z + v2z) / 3;

    let bestSolid = -1;
    let bestDistance = Infinity;
    score.fill(0);

    const nv0: [number, number, number] = [
      norm(v0x, geometryMin.x, geometrySize.x),
      norm(v0y, geometryMin.y, geometrySize.y),
      norm(v0z, geometryMin.z, geometrySize.z),
    ];
    const nv1: [number, number, number] = [
      norm(v1x, geometryMin.x, geometrySize.x),
      norm(v1y, geometryMin.y, geometrySize.y),
      norm(v1z, geometryMin.z, geometrySize.z),
    ];
    const nv2: [number, number, number] = [
      norm(v2x, geometryMin.x, geometrySize.x),
      norm(v2y, geometryMin.y, geometrySize.y),
      norm(v2z, geometryMin.z, geometrySize.z),
    ];
    const nc: [number, number, number] = [
      norm(centroid[0], geometryMin.x, geometrySize.x),
      norm(centroid[1], geometryMin.y, geometrySize.y),
      norm(centroid[2], geometryMin.z, geometrySize.z),
    ];

    for (let s = 0; s < solids.length; s++) {
      const bbox = normalizedSolidBounds[s];
      const v0In =
        nv0[0] >= bbox.min[0] - tolerance && nv0[0] <= bbox.max[0] + tolerance &&
        nv0[1] >= bbox.min[1] - tolerance && nv0[1] <= bbox.max[1] + tolerance &&
        nv0[2] >= bbox.min[2] - tolerance && nv0[2] <= bbox.max[2] + tolerance;
      const v1In =
        nv1[0] >= bbox.min[0] - tolerance && nv1[0] <= bbox.max[0] + tolerance &&
        nv1[1] >= bbox.min[1] - tolerance && nv1[1] <= bbox.max[1] + tolerance &&
        nv1[2] >= bbox.min[2] - tolerance && nv1[2] <= bbox.max[2] + tolerance;
      const v2In =
        nv2[0] >= bbox.min[0] - tolerance && nv2[0] <= bbox.max[0] + tolerance &&
        nv2[1] >= bbox.min[1] - tolerance && nv2[1] <= bbox.max[1] + tolerance &&
        nv2[2] >= bbox.min[2] - tolerance && nv2[2] <= bbox.max[2] + tolerance;
      const cIn =
        nc[0] >= bbox.min[0] - tolerance && nc[0] <= bbox.max[0] + tolerance &&
        nc[1] >= bbox.min[1] - tolerance && nc[1] <= bbox.max[1] + tolerance &&
        nc[2] >= bbox.min[2] - tolerance && nc[2] <= bbox.max[2] + tolerance;

      score[s] = (v0In ? 2 : 0) + (v1In ? 2 : 0) + (v2In ? 2 : 0) + (cIn ? 1 : 0);

      const center = solidCenters[s];
      const dx = nc[0] - center[0];
      const dy = nc[1] - center[1];
      const dz = nc[2] - center[2];
      const dist = dx * dx + dy * dy + dz * dz;

      if (score[s] > 0) {
        if (bestSolid < 0 || score[s] > score[bestSolid] || (score[s] === score[bestSolid] && dist < bestDistance)) {
          bestDistance = dist;
          bestSolid = s;
        }
      }
    }

    if (bestSolid < 0) {
      for (let s = 0; s < solids.length; s++) {
        const center = solidCenters[s];
        const dx = nc[0] - center[0];
        const dy = nc[1] - center[1];
        const dz = nc[2] - center[2];
        const dist = dx * dx + dy * dy + dz * dz;
        if (dist < bestDistance) {
          bestDistance = dist;
          bestSolid = s;
        }
      }
    }

    const builder = builders[Math.max(0, bestSolid)];
    const triIndices = [i0, i1, i2];

    triIndices.forEach((sourceIndex) => {
      let mapped = builder.vertexMap.get(sourceIndex);
      if (mapped === undefined) {
        mapped = builder.positions.length / 3;
        builder.vertexMap.set(sourceIndex, mapped);
        builder.positions.push(
          positionAttr.getX(sourceIndex),
          positionAttr.getY(sourceIndex),
          positionAttr.getZ(sourceIndex)
        );
        if (normalAttr) {
          builder.normals.push(
            normalAttr.getX(sourceIndex),
            normalAttr.getY(sourceIndex),
            normalAttr.getZ(sourceIndex)
          );
        }
      }
      builder.indices.push(mapped);
    });
  }

  builders.forEach((builder, solidIndex) => {
    if (builder.indices.length === 0) {
      out.set(solidIndex, geometry.clone());
      return;
    }

    const solidGeometry = new THREE.BufferGeometry();
    solidGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(builder.positions, 3)
    );
    if (normalAttr && builder.normals.length === builder.positions.length) {
      solidGeometry.setAttribute(
        "normal",
        new THREE.Float32BufferAttribute(builder.normals, 3)
      );
    }
    solidGeometry.setIndex(builder.indices);
    solidGeometry.computeVertexNormals();
    solidGeometry.normalizeNormals();
    solidGeometry.computeBoundingBox();
    solidGeometry.computeBoundingSphere();
    out.set(solidIndex, solidGeometry);
  });

  return out;
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
