"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { use3DGeometry } from "@/hooks/use3DGeometry";
import {
  createPartMeshes,
  createBufferGeometry,
} from "@/utils/geometry";
import { Skeleton } from "@/components/ui/skeleton";

// Quaternion-based OrbitControls implementation for smooth, intuitive rotation
function createOrbitControls(camera: THREE.PerspectiveCamera, element: HTMLElement) {
  const STATE = { NONE: -1, ROTATE: 0, ZOOM: 1 };
  let state = STATE.NONE;

  // Target point (center of rotation)
  const target = new THREE.Vector3(0, 0, 0);
  
  // Camera orientation stored as quaternion for smooth rotation
  const quat = new THREE.Quaternion();
  const quatInverse = new THREE.Quaternion();
  
  // Spherical coordinates for reference
  const spherical = new THREE.Spherical();
  spherical.setFromVector3(camera.position.clone().sub(target));
  
  // Store mouse position for delta calculation
  let lastX = 0;
  let lastY = 0;

  // Helper to update camera position from spherical coordinates
  const updateCameraPosition = () => {
    const offset = new THREE.Vector3();
    offset.setFromSphericalCoords(
      spherical.radius,
      spherical.phi,
      spherical.theta
    );
    camera.position.copy(target).add(offset);
    camera.lookAt(target);
  };

  const onMouseDown = (event: MouseEvent) => {
    if (event.button === 0) {
      state = STATE.ROTATE;
      lastX = event.clientX;
      lastY = event.clientY;
    }
  };

  const onMouseMove = (event: MouseEvent) => {
    if (state === STATE.ROTATE) {
      const deltaX = event.clientX - lastX;
      const deltaY = event.clientY - lastY;
      
      // Sensitivity of rotation (radians per pixel)
      const rotationSpeed = 0.005;
      
      // Update spherical angles based on mouse movement
      // Theta controls left-right rotation (horizontal)
      spherical.theta -= deltaX * rotationSpeed;
      
      // Phi controls up-down rotation (vertical), clamp to avoid gimbal lock
      spherical.phi -= deltaY * rotationSpeed;
      spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
      
      updateCameraPosition();
      
      lastX = event.clientX;
      lastY = event.clientY;
    }
  };

  const onMouseUp = () => {
    state = STATE.NONE;
  };

  const onWheel = (event: WheelEvent) => {
    event.preventDefault();
    
    // Zoom speed
    const zoomDelta = event.deltaY > 0 ? 1.1 : 0.9;
    spherical.radius *= zoomDelta;
    
    // Clamp zoom distance
    spherical.radius = Math.max(2, Math.min(50, spherical.radius));
    
    updateCameraPosition();
  };

  const onDoubleClick = () => {
    // Reset camera to default isometric view
    spherical.radius = 15;
    spherical.phi = Math.PI / 4;      // 45 degrees from top
    spherical.theta = Math.PI / 4;    // 45 degrees around
    updateCameraPosition();
  };

  const handleMouseDown = (e: MouseEvent) => {
    onMouseDown(e);
  };

  const handleMouseMove = (e: MouseEvent) => {
    onMouseMove(e);
  };

  const handleMouseUp = () => {
    onMouseUp();
  };

  const handleWheel = (e: WheelEvent) => {
    onWheel(e);
  };

  const handleDoubleClick = () => {
    onDoubleClick();
  };

  element.addEventListener("mousedown", handleMouseDown);
  element.addEventListener("mousemove", handleMouseMove);
  element.addEventListener("mouseup", handleMouseUp);
  element.addEventListener("wheel", handleWheel, { passive: false });
  element.addEventListener("dblclick", handleDoubleClick);

  return {
    dispose: () => {
      element.removeEventListener("mousedown", handleMouseDown);
      element.removeEventListener("mousemove", handleMouseMove);
      element.removeEventListener("mouseup", handleMouseUp);
      element.removeEventListener("wheel", handleWheel);
      element.removeEventListener("dblclick", handleDoubleClick);
    }
  };
}

interface GeometryViewerProps {
  modelId: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  explosionValue?: number;
  selectedPartId?: number;
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
  explosionValue = 0,
  selectedPartId,
}: GeometryViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const meshesRef = useRef<Map<number, THREE.Mesh>>(new Map());
  const animationIdRef = useRef<number | null>(null);
  const originalPositionsRef = useRef<Map<number, THREE.Vector3>>(new Map());

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

       // Initialize OrbitControls
       const controls = createOrbitControls(camera, renderer.domElement);
       console.log("[GeometryViewer] OrbitControls initialized");

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
          controls.dispose();
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

  // Handle part selection highlighting
  useEffect(() => {
    if (!meshesRef.current || meshesRef.current.size === 0) {
      return;
    }

    // Smooth color transition for selected parts
    const transitionSpeed = 0.1;

    meshesRef.current.forEach((mesh, partIndex) => {
      if (mesh.material && !Array.isArray(mesh.material)) {
        const material = mesh.material as THREE.MeshPhongMaterial;
        const targetColor = partIndex === selectedPartId 
          ? { r: 0.54, g: 0.42, b: 0.66 } // Dark purple: 0x8a6ba8
          : { r: 0.8, g: 0.8, b: 0.8 }; // Light gray: 0xcccccc

        // Smooth transition to target color
        const currentColor = material.color;
        currentColor.r += (targetColor.r - currentColor.r) * transitionSpeed;
        currentColor.g += (targetColor.g - currentColor.g) * transitionSpeed;
        currentColor.b += (targetColor.b - currentColor.b) * transitionSpeed;

        // Add emissive glow for selected parts
        if (partIndex === selectedPartId) {
          material.emissive.setHex(0x5a4b78);
        } else {
          material.emissive.setHex(0x000000);
        }
      }
    });
  }, [selectedPartId]);

  // Handle explosion value changes
  useEffect(() => {
    if (!sceneRef.current || !meshesRef.current || meshesRef.current.size === 0) {
      return;
    }

    // If no original positions saved, save them now
    if (originalPositionsRef.current.size === 0) {
      meshesRef.current.forEach((mesh, index) => {
        originalPositionsRef.current.set(index, mesh.position.clone());
      });
    }

    // Apply explosion effect
    meshesRef.current.forEach((mesh, index) => {
      const originalPos = originalPositionsRef.current.get(index);
      if (!originalPos) return;

      // Calculate explosion direction (away from origin)
      const bbox = new THREE.Box3().setFromObject(mesh);
      const center = bbox.getCenter(new THREE.Vector3());
      const explosionDir = center.normalize();

      // Calculate new position based on explosion value (0-100)
      const explosionAmount = (explosionValue / 100) * 3; // Max 3 units
      const newPos = originalPos
        .clone()
        .add(explosionDir.multiplyScalar(explosionAmount));

      mesh.position.copy(newPos);
    });
  }, [explosionValue]);

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
