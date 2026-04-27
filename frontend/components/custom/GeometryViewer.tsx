"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { use3DGeometry } from "@/hooks/use3DGeometry";
import {
  createSolidMeshes,
  mapPartsToSolidIndices,
  createBufferGeometry,
} from "@/utils/geometry";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";

// Quaternion-based OrbitControls implementation for smooth, intuitive rotation
interface OrbitController {
  dispose: () => void;
  setMode: (mode: "fixed" | "free") => void;
}

function createOrbitControls(
  camera: THREE.PerspectiveCamera | THREE.OrthographicCamera,
  element: HTMLElement
) {
  const STATE = { NONE: -1, ROTATE: 0, PAN: 1 };
  let state = STATE.NONE;
  let mode: "fixed" | "free" = "fixed";

  // Target point (center of rotation)
  const target = new THREE.Vector3(0, 0, 0);
  
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
    if (event.button === 0 && event.shiftKey) {
      state = STATE.PAN;
      lastX = event.clientX;
      lastY = event.clientY;
    } else if (event.button === 0) {
      state = STATE.ROTATE;
      lastX = event.clientX;
      lastY = event.clientY;
    } else if (event.button === 1 || event.button === 2) {
      state = STATE.PAN;
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
      
      if (mode === "fixed") {
        // Quaternion/orbit mode with fixed up vector
        spherical.theta -= deltaX * rotationSpeed;
        spherical.phi -= deltaY * rotationSpeed;
        spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
        camera.up.set(0, 1, 0);
        updateCameraPosition();
      } else {
        // Free orbit mode
        const offset = camera.position.clone().sub(target);
        const localX = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).normalize();
        const localY = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion).normalize();
        const qYaw = new THREE.Quaternion().setFromAxisAngle(localY, -deltaX * rotationSpeed);
        const qPitch = new THREE.Quaternion().setFromAxisAngle(localX, -deltaY * rotationSpeed);
        const q = qYaw.multiply(qPitch);

        offset.applyQuaternion(q);
        camera.up.applyQuaternion(q).normalize();
        camera.position.copy(target).add(offset);
        camera.lookAt(target);
        spherical.setFromVector3(camera.position.clone().sub(target));
      }
    } else if (state === STATE.PAN) {
      const deltaX = event.clientX - lastX;
      const deltaY = event.clientY - lastY;
      const offset = camera.position.clone().sub(target);
      const distance = Math.max(offset.length(), 1);
      const panScale = distance * 0.0015;

      const right = new THREE.Vector3(1, 0, 0)
        .applyQuaternion(camera.quaternion)
        .normalize()
        .multiplyScalar(-deltaX * panScale);
      const up = new THREE.Vector3(0, 1, 0)
        .applyQuaternion(camera.quaternion)
        .normalize()
        .multiplyScalar(deltaY * panScale);

      const pan = right.add(up);
      camera.position.add(pan);
      target.add(pan);
      camera.lookAt(target);
      spherical.setFromVector3(camera.position.clone().sub(target));
    }

    if (state !== STATE.NONE) {
      lastX = event.clientX;
      lastY = event.clientY;
    }
  };

  const onMouseUp = () => {
    state = STATE.NONE;
  };

  const onWheel = (event: WheelEvent) => {
    event.preventDefault();

    if ((camera as THREE.OrthographicCamera).isOrthographicCamera) {
      const ortho = camera as THREE.OrthographicCamera;
      const zoomDelta = event.deltaY > 0 ? 0.9 : 1.1;
      ortho.zoom = Math.max(0.25, Math.min(8, ortho.zoom * zoomDelta));
      ortho.updateProjectionMatrix();
    } else {
      const zoomDelta = event.deltaY > 0 ? 1.1 : 0.9;
      spherical.radius *= zoomDelta;
      spherical.radius = Math.max(2, Math.min(50, spherical.radius));
      updateCameraPosition();
    }
  };

  const onDoubleClick = () => {
    // Reset camera to default isometric view
    spherical.radius = 15;
    spherical.phi = Math.PI / 4;      // 45 degrees from top
    spherical.theta = Math.PI / 4;    // 45 degrees around
    camera.up.set(0, 1, 0);
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

  const handleContextMenu = (e: MouseEvent) => {
    e.preventDefault();
  };

  element.addEventListener("mousedown", handleMouseDown);
  element.addEventListener("mousemove", handleMouseMove);
  element.addEventListener("mouseup", handleMouseUp);
  element.addEventListener("wheel", handleWheel, { passive: false });
  element.addEventListener("dblclick", handleDoubleClick);
  element.addEventListener("contextmenu", handleContextMenu);

  return {
    dispose: () => {
      element.removeEventListener("mousedown", handleMouseDown);
      element.removeEventListener("mousemove", handleMouseMove);
      element.removeEventListener("mouseup", handleMouseUp);
      element.removeEventListener("wheel", handleWheel);
      element.removeEventListener("dblclick", handleDoubleClick);
      element.removeEventListener("contextmenu", handleContextMenu);
    },
    setMode: (newMode: "fixed" | "free") => {
      mode = newMode;
      if (mode === "fixed") {
        camera.up.set(0, 1, 0);
        spherical.setFromVector3(camera.position.clone().sub(target));
        updateCameraPosition();
      }
    },
  } as OrbitController;
}

interface GeometryViewerProps {
  modelId: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  explosionValue?: number;
  selectedPartId?: number;
  selectedPartIds?: number[];
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
  explosionValue = 42,
  selectedPartId,
  selectedPartIds,
}: GeometryViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const orthoCameraRef = useRef<THREE.OrthographicCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitController | null>(null);
  const meshesRef = useRef<Map<number, THREE.Mesh>>(new Map());
  const animationIdRef = useRef<number | null>(null);
  const originalPositionsRef = useRef<Map<number, THREE.Vector3>>(new Map());

  const {
    geometry,
    parts,
    partToSolidMap,
    isLoading,
    error: geometryError,
  } = use3DGeometry({
    modelId,
  });

  const [error, setError] = useState<string | null>(null);
  const [orbitMode, setOrbitMode] = useState<"fixed" | "free">(() => {
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem("viewer:orbitMode");
      if (saved === "fixed" || saved === "free") {
        return saved;
      }
    }
    return "fixed";
  });
  const [projectionMode, setProjectionMode] = useState<"perspective" | "ortho">(() => {
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem("viewer:projectionMode");
      if (saved === "perspective" || saved === "ortho") {
        return saved;
      }
    }
    return "ortho";
  });

  const persistOrbitMode = (mode: "fixed" | "free") => {
    setOrbitMode(mode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("viewer:orbitMode", mode);
    }
  };

  const persistProjectionMode = (mode: "perspective" | "ortho") => {
    setProjectionMode(mode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("viewer:projectionMode", mode);
    }
  };

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
       scene.background = new THREE.Color(0xf8faf9); // Bright snow 700 background

       // Camera setup
       const perspectiveCamera = new THREE.PerspectiveCamera(
         75,
         width / height,
         0.1,
         10000
       );
       perspectiveCamera.position.set(0, 0, 10);

       const frustumSize = 12;
       const aspect = width / height;
       const orthoCamera = new THREE.OrthographicCamera(
         (-frustumSize * aspect) / 2,
         (frustumSize * aspect) / 2,
         frustumSize / 2,
         -frustumSize / 2,
         -1000,
         1000
       );
       orthoCamera.position.copy(perspectiveCamera.position);
       orthoCamera.lookAt(0, 0, 0);

       const camera = projectionMode === "ortho" ? orthoCamera : perspectiveCamera;

       // Renderer setup
       const renderer = new THREE.WebGLRenderer({
         antialias: true,
         alpha: true,
         preserveDrawingBuffer: true,
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
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.35);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.65);
        directionalLight.position.set(5, 8, 4);
        scene.add(directionalLight);

        // Visible point light source
        const pointLight = new THREE.PointLight(0xfff4d6, 1.4, 120, 2);
        pointLight.position.set(7, 9, 6);
        scene.add(pointLight);

        const lightBulb = new THREE.Mesh(
          new THREE.SphereGeometry(0.14, 16, 16),
          new THREE.MeshBasicMaterial({ color: 0xffe6a8 })
        );
        lightBulb.position.copy(pointLight.position);
        scene.add(lightBulb);

        // XZ reference plane with grid markings
        const gridHelper = new THREE.GridHelper(24, 24, 0x6f6971, 0xa7a2a9);
        gridHelper.position.set(0, -3.2, 0);
        scene.add(gridHelper);

        // Up-direction arrow (+Y)
        const upArrow = new THREE.ArrowHelper(
          new THREE.Vector3(0, 1, 0),
          new THREE.Vector3(-5.5, -3.1, -5.5),
          2.2,
          0x1ea55b,
          0.45,
          0.25
        );
        scene.add(upArrow);

       // Initialize OrbitControls
        const controls = createOrbitControls(camera, renderer.domElement);
        controls.setMode(orbitMode);
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

      // Fit model to view using mesh transforms (do not mutate source geometry,
      // because solid bounding boxes are in backend coordinates)
      bufferGeometry.computeBoundingBox();
      const bbox = bufferGeometry.boundingBox;
      let modelCenter = new THREE.Vector3();
      let modelScale = 1;
      if (bbox) {
        bbox.getCenter(modelCenter);
        const size = new THREE.Vector3();
        bbox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        modelScale = 5 / maxDim;
      }

          const solids = geometry.metadata.solids;
          const meshes = createSolidMeshes(bufferGeometry, solids);

         meshes.forEach((mesh, solidIndex) => {
            mesh.scale.setScalar(modelScale);
            mesh.position.copy(modelCenter).multiplyScalar(-modelScale);

            const localCenter = mesh.userData.localCenter as THREE.Vector3 | undefined;
            const dir = localCenter
              ? localCenter.clone().sub(modelCenter)
              : new THREE.Vector3(
                  Math.cos((solidIndex / Math.max(meshes.size, 1)) * Math.PI * 2),
                  0.2,
                  Math.sin((solidIndex / Math.max(meshes.size, 1)) * Math.PI * 2)
                );
            if (dir.lengthSq() < 1e-5) {
              dir.set(1, 0, 0);
            }
            mesh.userData.explosionDirection = dir.normalize();
            mesh.userData.isSelected = false;
          });

          console.log(`[GeometryViewer] Created ${meshes.size} solid meshes`);
          meshes.forEach((mesh) => {
            scene.add(mesh);
          });
        meshesRef.current = meshes;
        controlsRef.current = controls;

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
        if ((camera as THREE.PerspectiveCamera).isPerspectiveCamera) {
          const perspective = camera as THREE.PerspectiveCamera;
          perspective.aspect = newWidth / newHeight;
          perspective.updateProjectionMatrix();
        } else {
          const ortho = camera as THREE.OrthographicCamera;
          const frustumSize = 12;
          const aspect = newWidth / Math.max(newHeight, 1);
          ortho.left = (-frustumSize * aspect) / 2;
          ortho.right = (frustumSize * aspect) / 2;
          ortho.top = frustumSize / 2;
          ortho.bottom = -frustumSize / 2;
          ortho.updateProjectionMatrix();
        }
        renderer.setSize(newWidth, newHeight);
      };

      window.addEventListener("resize", handleResize);

      sceneRef.current = scene;
       cameraRef.current = perspectiveCamera;
       orthoCameraRef.current = orthoCamera;
      rendererRef.current = renderer;

      if (onLoad) onLoad();

        return () => {
          window.removeEventListener("resize", handleResize);
          if (animationIdRef.current) {
            cancelAnimationFrame(animationIdRef.current);
          }
          controls.dispose();
          controlsRef.current = null;
          if (containerRef.current && rendererRef.current) {
            try {
              containerRef.current.removeChild(rendererRef.current.domElement);
            } catch (e) {
              // Already removed
            }
          }
           bufferGeometry.dispose();
           meshes.forEach((mesh) => {
             if (mesh.geometry) {
               mesh.geometry.dispose();
             }
             if (mesh.material && !Array.isArray(mesh.material)) {
               (mesh.material as THREE.Material).dispose();
             }
           });
           renderer.dispose();
        };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to render geometry";
      setError(message);
      if (onError) {
        onError(new Error(message));
      }
    }
  }, [geometry, parts, partToSolidMap, isLoading, onLoad, onError, projectionMode]);

  // Handle part selection highlighting
  useEffect(() => {
    if (!meshesRef.current || meshesRef.current.size === 0) {
      return;
    }

    const solids = geometry?.metadata?.solids ?? [];
    const partToSolidCandidates = parts ? mapPartsToSolidIndices(parts, solids) : new Map<number, number[]>();
    const selectedSolidSet = new Set<number>();

    const allSelectedPartIds = new Set<number>([
      ...(selectedPartIds ?? []),
      ...(selectedPartId !== undefined && selectedPartId !== null ? [selectedPartId] : []),
    ]);

    allSelectedPartIds.forEach((partIndex) => {
      (partToSolidCandidates.get(partIndex) ?? []).forEach((solidIndex) => {
        selectedSolidSet.add(solidIndex);
      });
    });

    meshesRef.current.forEach((mesh, solidIndex) => {
      if (mesh.material && !Array.isArray(mesh.material)) {
        const material = mesh.material as THREE.MeshPhongMaterial;
        const isSelected = selectedSolidSet.has(solidIndex);
        material.color.setHex(isSelected ? 0xff3030 : 0xa7a2a9);

        if (isSelected) {
          material.emissive.setHex(0xff0000);
          material.emissiveIntensity = 1.1;
        } else {
          material.emissive.setHex(0x000000);
          material.emissiveIntensity = 0;
        }
      }
    });

  }, [selectedPartId, selectedPartIds, geometry, parts]);

  useEffect(() => {
    controlsRef.current?.setMode(orbitMode);
  }, [orbitMode]);

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

      const maxExplosionDistance = 3;

      meshesRef.current.forEach((mesh, index) => {
        const originalPos = originalPositionsRef.current.get(index);
        if (!originalPos) return;

        const directionFromCenter = (mesh.userData.explosionDirection as THREE.Vector3 | undefined)
          ?.clone()
          .normalize() ??
          new THREE.Vector3(
            Math.cos((index / Math.max(meshesRef.current.size, 1)) * Math.PI * 2),
            0.2,
            Math.sin((index / Math.max(meshesRef.current.size, 1)) * Math.PI * 2)
          ).normalize();

        const explosionDistance = (explosionValue / 100) * maxExplosionDistance;
        const explosionOffset = directionFromCenter.multiplyScalar(explosionDistance);

        mesh.position.copy(originalPos).add(explosionOffset);
      });
    }, [explosionValue]);

  if (error) {
    return (
      <div className="w-full rounded-3xl bg-red-50 p-6 flex items-center justify-center"
        style={{ aspectRatio: "4 / 3" }}>
        <div className="text-center">
          <p className="text-red-700 font-semibold">Błąd przy ładowaniu modelu 3D</p>
          <p className="text-red-600 text-sm mt-2">{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full rounded-3xl bg-bright_snow-600 overflow-hidden"
        style={{ aspectRatio: "4 / 3" }}>
        <Skeleton className="w-full h-full" />
      </div>
    );
  }

  return (
    <div className="relative w-full">
      <div
        ref={containerRef}
        data-pdf-capture="geometry-surface"
        className="w-full rounded-3xl bg-bright_snow-600 overflow-hidden"
        style={{ 
          aspectRatio: "4 / 3",
          minHeight: "280px",
        }}
      />

      <div className="absolute top-3 right-3 z-30 max-w-[360px] rounded-xl bg-carbon_black-DEFAULT/75 text-bright_snow-900 px-3 py-2 text-xs leading-tight backdrop-blur-sm">
        <p>Obróć: przeciągnij | Przesuń: shift+przeciągnij | Powiększ: scroll | Reset: 2x klik</p>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-[11px]">Tryb obrotu:</span>
          <Switch
            checked={orbitMode === "free"}
            onCheckedChange={(checked) => persistOrbitMode(checked ? "free" : "fixed")}
          />
          <span className="text-[11px]">{orbitMode === "fixed" ? "Quaternion" : "Free"}</span>
        </div>
        <div className="mt-1 flex items-center gap-2">
          <span className="text-[11px]">Kamera:</span>
          <Switch
            checked={projectionMode === "ortho"}
            onCheckedChange={(checked) => persistProjectionMode(checked ? "ortho" : "perspective")}
          />
          <span className="text-[11px]">{projectionMode === "perspective" ? "Persp" : "Ortho"}</span>
        </div>
      </div>
    </div>
  );
}
