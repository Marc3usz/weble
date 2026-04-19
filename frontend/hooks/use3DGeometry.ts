import { useState, useEffect, useCallback } from "react";
import { getGeometry, getParts } from "@/services/api";
import { Geometry, Part } from "@/types";
import { spatialMatchPartsToBoundingBoxes } from "@/utils/geometry";

interface Use3DGeometryOptions {
  modelId: string;
  enabled?: boolean;
}

interface GeometryData {
  geometry: Geometry | null;
  parts: Part[] | null;
  partToSolidMap: Map<number, number> | null; // Maps part index to solid index
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook to load 3D geometry and parts data, then spatially match parts to geometry solids
 * 
 * TODO: Add caching layer to prevent re-fetching same geometry
 * TODO: Add geometry validation to catch malformed data early
 */
export function use3DGeometry({
  modelId,
  enabled = true,
}: Use3DGeometryOptions): GeometryData {
  const [geometry, setGeometry] = useState<Geometry | null>(null);
  const [parts, setParts] = useState<Part[] | null>(null);
  const [partToSolidMap, setPartToSolidMap] = useState<Map<number, number> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !modelId) return;

    const loadGeometry = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log(`[use3DGeometry] Loading geometry for modelId: ${modelId}`);

        // Load geometry and parts in parallel
        const [geometryData, partsData] = await Promise.all([
          getGeometry(modelId),
          getParts(modelId),
        ]);

        console.log("[use3DGeometry] Loaded geometry data:", {
          vertexCount: geometryData.vertices.length,
          solids: geometryData.metadata.solids.length,
        });
        console.log("[use3DGeometry] Loaded parts data:", partsData.parts.length);

        setGeometry(geometryData);
        setParts(partsData.parts);

        // Spatially match parts to solids in geometry
        const map = spatialMatchPartsToBoundingBoxes(
          partsData.parts,
          geometryData.metadata.solids
        );
        setPartToSolidMap(map);
        console.log("[use3DGeometry] Spatial matching complete");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load geometry";
        setError(message);
        console.error("[use3DGeometry] Error loading geometry:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadGeometry();
  }, [modelId, enabled]);

  return {
    geometry,
    parts,
    partToSolidMap,
    isLoading,
    error,
  };
}
