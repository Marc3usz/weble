"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { use3DGeometry } from "@/hooks/use3DGeometry";
import {
  createPartMeshes,
  createBufferGeometry,
} from "@/utils/geometry";
import { Skeleton } from "@/components/ui/skeleton";

interface GeometryViewerProps {
  modelId: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

/**
 * 3D Geometry Viewer Component
 * 
 * Loads geometry from backend, spatially matches parts to solids, and renders
 * per-part meshes in Three.js scene.
 * 
 * MVP Features:
 * - Load geometry and parts data
 * - Create per-part meshes (currently using full geometry for each)
 * - Basic Three.js scene with lighting
 * - Responsive canvas sizing
 * - Error handling and loading states
 * 
 * TODO: Add OrbitControls for camera interaction (pan/zoom/rotate)
 * TODO: Add part selection and highlighting (change material colors)
 * TODO: Add explode/collapse animation (calculate and animate positions)
 * TODO: Add viewport resizing with proper animation frame cleanup
 * TODO: Add frustum culling for performance with 100+ parts
 * TODO: Implement hover detection for part tooltips
 * TODO: Add animated camera transitions to focus on specific parts
 */
export function GeometryViewer({
  modelId,
  onLoad,
  onError,
}: GeometryViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const meshesRef = useRef<Map<number, THREE.Mesh>>(new Map());
  const animationIdRef = useRef<number | null>(null);

  const { geometry, parts, isLoading, error: geometryError } = use3DGeometry({
    modelId,
  });

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (geometryError) {
      console.error("[GeometryViewer] Geometry loading error:", geometryError);
      setError(geometryError);
      if (onError) {
        onError(new Error(geometryError));
      }
    }
  }, [geometryError, onError]);

  useEffect(() => {
    console.log("[GeometryViewer] Component state:", {
      geometry: geometry ? "loaded" : "null",
      parts: parts ? parts.length : "null",
      isLoading,
      containerWidth: containerRef.current?.clientWidth,
      containerHeight: containerRef.current?.clientHeight,
    });
  }, [geometry, parts, isLoading]);

   useEffect(() => {
     if (!containerRef.current || !geometry || !parts || isLoading) return;

     try {
       // Clean up previous scene if it exists
       if (sceneRef.current && rendererRef.current) {
         if (animationIdRef.current) {
           cancelAnimationFrame(animationIdRef.current);
         }
         // Safely remove the canvas from DOM
         if (containerRef.current && rendererRef.current.domElement && 
             rendererRef.current.domElement.parentNode === containerRef.current) {
           containerRef.current.removeChild(rendererRef.current.domElement);
         }
         rendererRef.current.dispose();
       }

       const width = containerRef.current.clientWidth;
       const height = containerRef.current.clientHeight;
       
       // Guard against zero dimensions
       if (width === 0 || height === 0) {
         console.warn("Container has zero dimensions, skipping geometry render");
         return;
       }

      // Scene setup
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xfafaf8); // Light background

      // Camera setup
      const camera = new THREE.PerspectiveCamera(
        75,
        width / height,
        0.1,
        10000
      );
      camera.position.set(0, 0, 10);

       // Renderer setup
       const renderer = new THREE.WebGLRenderer({
         antialias: true,
         alpha: true,
       });
       renderer.setSize(width, height);
       renderer.setPixelRatio(window.devicePixelRatio);
       console.log("[GeometryViewer] Three.js setup complete:", {
         width,
         height,
         pixelRatio: window.devicePixelRatio,
       });
       containerRef.current.appendChild(renderer.domElement);

      // Lighting
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(5, 5, 5);
      scene.add(directionalLight);

       // Create buffer geometry from raw data
       console.log("[GeometryViewer] Creating buffer geometry from:", {
         vertexCount: geometry.vertices.length,
         normalCount: geometry.normals.length,
         indexCount: geometry.indices.length,
       });
       const bufferGeometry = createBufferGeometry(
         geometry.vertices,
         geometry.normals,
         geometry.indices
       );

      // Center and fit geometry to view
      bufferGeometry.computeBoundingBox();
      const bbox = bufferGeometry.boundingBox;
      if (bbox) {
        const center = new THREE.Vector3();
        bbox.getCenter(center);
        bufferGeometry.translate(-center.x, -center.y, -center.z);

        const size = new THREE.Vector3();
        bbox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 5 / maxDim;
        bufferGeometry.scale(scale, scale, scale);
      }

       // Create per-part meshes
       // TODO: Replace with actual per-part geometry extraction when backend provides vertex ranges
       const meshes = createPartMeshes(bufferGeometry, parts);
       console.log(`[GeometryViewer] Created ${meshes.size} part meshes`);
       meshes.forEach((mesh) => {
         scene.add(mesh);
       });
       meshesRef.current = meshes;

       // Animation loop
       let frameCount = 0;
       const animate = () => {
         frameCount++;
         if (frameCount % 100 === 0) {
           console.log(`[GeometryViewer] Animation frame ${frameCount}`);
         }
         animationIdRef.current = requestAnimationFrame(animate);
         renderer.render(scene, camera);
       };
       console.log("[GeometryViewer] Starting animation loop");
       animate();

      // Handle window resize
      const handleResize = () => {
        if (!containerRef.current || !renderer) return;
        const newWidth = containerRef.current.clientWidth;
        const newHeight = containerRef.current.clientHeight;
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
      };

      window.addEventListener("resize", handleResize);

      sceneRef.current = scene;
      cameraRef.current = camera;
      rendererRef.current = renderer;

      if (onLoad) onLoad();

       return () => {
         window.removeEventListener("resize", handleResize);
         if (animationIdRef.current) {
           cancelAnimationFrame(animationIdRef.current);
         }
         if (containerRef.current && rendererRef.current) {
           try {
             containerRef.current.removeChild(rendererRef.current.domElement);
           } catch (e) {
             // Already removed
           }
         }
         bufferGeometry.dispose();
         // Dispose shared material (only once, since all meshes use the same one)
         const firstMesh = meshes.values().next().value;
         if (firstMesh?.material && !Array.isArray(firstMesh.material)) {
           (firstMesh.material as THREE.Material).dispose();
         }
         renderer.dispose();
       };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to render geometry";
      setError(message);
      if (onError) {
        onError(new Error(message));
      }
    }
  }, [geometry, parts, isLoading, onLoad, onError]);

  if (error) {
    return (
      <div className="w-full rounded-3xl bg-red-50 border border-red-200 p-6 flex items-center justify-center"
        style={{ aspectRatio: "1" }}>
        <div className="text-center">
          <p className="text-red-700 font-semibold">Błąd przy ładowaniu modelu 3D</p>
          <p className="text-red-600 text-sm mt-2">{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full rounded-3xl bg-bright_snow-600 border border-lilac_ash-200 overflow-hidden"
        style={{ aspectRatio: "1" }}>
        <Skeleton className="w-full h-full" />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full rounded-3xl bg-bright_snow-600 border border-lilac_ash-200 overflow-hidden"
      style={{ 
        aspectRatio: "1",
        minHeight: "200px", // Ensure minimum size for canvas
      }}
    />
  );
}
