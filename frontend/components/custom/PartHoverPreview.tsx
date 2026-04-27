"use client";

import React, { useEffect, useState, useRef } from "react";
import { createPortal } from "react-dom";
import * as THREE from "three";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Part } from "@/types";
import { use3DGeometry } from "@/hooks/use3DGeometry";
import { createBufferGeometry, createSolidMeshes, mapPartsToSolidIndices } from "@/utils/geometry";

interface PartHoverPreviewProps {
  modelId: string;
  partIndex: number;
  part: Part;
  visible: boolean;
  anchorRect: DOMRect | null;
  delay?: number; // Delay in milliseconds before showing preview
}

/**
 * Part Hover Preview Popup
 * 
 * Shows detailed part information next to the hovered part card.
 * Appears after 2s mouse idle (configurable via delay prop).
 * 
 * Features:
 * - Fade in/fade out animation
 * - Positioned next to parent part card
 * - Shows part type, volume, dimensions
 * - Part image/SVG if available
 * 
 * TODO: Add caching to prevent recreating preview on repeated hovers
 * TODO: Add keyboard support (show/hide with arrow keys)
 * TODO: Add smooth position transitions as scroll changes
 */
export function PartHoverPreview({
  modelId,
  partIndex,
  part,
  visible,
  anchorRect,
  delay = 500,
}: PartHoverPreviewProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewReady, setPreviewReady] = useState(false);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  const { geometry, parts, partToSolidMap, isLoading } = use3DGeometry({
    modelId,
    enabled: showPreview,
  });

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!visible) {
      setShowPreview(false);
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
      return;
    }

    // Start idle timer when hovering
    idleTimerRef.current = setTimeout(() => {
      setShowPreview(true);
    }, delay);

    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [visible, delay]);

  useEffect(() => {
    if (!showPreview) {
      setPreviewReady(false);
      setPreviewError(null);
    }
  }, [showPreview]);

  useEffect(() => {
    if (!showPreview || !canvasContainerRef.current || !geometry || !parts || parts.length === 0) {
      return;
    }

    setPreviewError(null);
    setPreviewReady(false);

    const container = canvasContainerRef.current;
    const width = Math.max(container.clientWidth, 280);
    const height = Math.max(container.clientHeight, 140);

    try {
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);

      const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      camera.position.set(0, 0, 6);
      camera.lookAt(0, 0, 0);

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setSize(width, height);
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.domElement.style.width = "100%";
      renderer.domElement.style.height = "100%";
      renderer.domElement.style.display = "block";
      renderer.domElement.style.background = "#ffffff";
      renderer.domElement.style.pointerEvents = "none";
      container.appendChild(renderer.domElement);

      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.25;

      const hemiLight = new THREE.HemisphereLight(0xffffff, 0xf2f2f2, 0.9);
      scene.add(hemiLight);

      const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
      keyLight.position.set(4, 6, 5);
      scene.add(keyLight);

      const fillLight = new THREE.PointLight(0xffffff, 0.9, 60, 2);
      fillLight.position.set(-3.5, 2.8, 3.2);
      scene.add(fillLight);

      const rimLight = new THREE.PointLight(0xffffff, 0.8, 60, 2);
      rimLight.position.set(2.8, 2.4, -4.2);
      scene.add(rimLight);

      const baseGeometry = createBufferGeometry(
        geometry.vertices,
        geometry.normals,
        geometry.indices
      );

      const partMap = mapPartsToSolidIndices(parts, geometry.metadata.solids);
      const candidateSolids = partMap.get(partIndex) ?? [];
      const mappedFromLegacy = partToSolidMap?.get(partIndex);
      const solidOrder = [...candidateSolids, ...(mappedFromLegacy !== undefined ? [mappedFromLegacy] : [])];

      const solidMeshes = createSolidMeshes(baseGeometry, geometry.metadata.solids);
      let partGeometry: THREE.BufferGeometry | null = null;
      let chosenSolidIndex: number | null = null;

      for (const solidIndex of solidOrder) {
        const mesh = solidMeshes.get(solidIndex);
        if (!mesh?.geometry) continue;
        const source = mesh.geometry as THREE.BufferGeometry;
        const positionAttr = source.getAttribute("position") as THREE.BufferAttribute | undefined;
        if (positionAttr && positionAttr.count > 0 && (source.getIndex()?.count ?? 0) >= 3) {
          partGeometry = source.clone();
          chosenSolidIndex = solidIndex;
          break;
        }
      }

      if (!partGeometry) {
        const firstMesh = solidMeshes.values().next().value as THREE.Mesh | undefined;
        if (firstMesh?.geometry) {
          partGeometry = (firstMesh.geometry as THREE.BufferGeometry).clone();
        }
      }

      solidMeshes.forEach((mesh) => {
        if (mesh.material && !Array.isArray(mesh.material)) {
          (mesh.material as THREE.Material).dispose();
        }
        if (mesh.geometry) {
          mesh.geometry.dispose();
        }
      });

      if (!partGeometry) {
        baseGeometry.dispose();
        renderer.dispose();
        if (renderer.domElement.parentNode === container) {
          container.removeChild(renderer.domElement);
        }
        setPreviewError("Brak podglądu siatki dla tej części");
        return;
      }

      console.log("[PartHoverPreview] Rendering solid", {
        partIndex,
        chosenSolidIndex,
        candidateSolids,
        triangles: (partGeometry.getIndex()?.count ?? 0) / 3,
        vertexCount: (partGeometry.getAttribute("position") as THREE.BufferAttribute | undefined)?.count ?? 0,
      });

      // Normalize into stable preview space so world-scale doesn't break camera/frustum.
      partGeometry.computeBoundingBox();
      partGeometry.computeBoundingSphere();
      const bbox = partGeometry.boundingBox;
      const sphere = partGeometry.boundingSphere;

      if (!bbox || !sphere || !Number.isFinite(sphere.radius) || sphere.radius <= 0) {
        throw new Error("Invalid part geometry bounds for preview");
      }

      const normalizedGeometry = partGeometry.clone();
      const center = bbox.getCenter(new THREE.Vector3());
      const safeRadius = Math.max(sphere.radius, 1e-4);
      const normalizeScale = 1 / safeRadius;
      normalizedGeometry.translate(-center.x, -center.y, -center.z);
      normalizedGeometry.scale(normalizeScale, normalizeScale, normalizeScale);

      const mesh = new THREE.Mesh(
        normalizedGeometry,
        new THREE.MeshStandardMaterial({
          color: 0xff0000,
          emissive: 0x220000,
          emissiveIntensity: 0.18,
          roughness: 0.45,
          metalness: 0.0,
          side: THREE.DoubleSide,
        })
      );
      mesh.frustumCulled = false;

      const edgeLines = new THREE.LineSegments(
        new THREE.EdgesGeometry(normalizedGeometry, 25),
        new THREE.LineBasicMaterial({ color: 0x111111, transparent: true, opacity: 0.95 })
      );
      edgeLines.frustumCulled = false;

      const camDist = 2.8;
      camera.position.set(camDist * 1.0, camDist * 0.75, camDist * 1.1);
      camera.near = 0.01;
      camera.far = 120;
      camera.updateProjectionMatrix();
      camera.lookAt(0, 0, 0);

      // Axis alignment: y-up, x left-right, z depth.
      // We use x-axis as quaternion pole for animated spin.
      const axis = new THREE.Vector3(1, 0, 0);
      scene.add(mesh);
      scene.add(edgeLines);

      let markedReady = false;
      renderer.render(scene, camera);

      const animate = () => {
        const t = performance.now() * 0.0005;
        mesh.quaternion.setFromAxisAngle(axis, t);
        edgeLines.quaternion.copy(mesh.quaternion);
        renderer.render(scene, camera);
        if (!markedReady) {
          markedReady = true;
          setPreviewReady(true);
        }
        animationFrameRef.current = requestAnimationFrame(animate);
      };
      animate();

      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        renderer.dispose();
        if (mesh.material && !Array.isArray(mesh.material)) {
          mesh.material.dispose();
        }
        if (edgeLines.geometry) {
          edgeLines.geometry.dispose();
        }
        if (edgeLines.material && !Array.isArray(edgeLines.material)) {
          edgeLines.material.dispose();
        }
        normalizedGeometry.dispose();
        partGeometry.dispose();
        baseGeometry.dispose();
        if (renderer.domElement.parentNode === container) {
          container.removeChild(renderer.domElement);
        }
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Błąd podglądu 3D";
      setPreviewError(message);
      return;
    }
  }, [showPreview, geometry, parts, partToSolidMap, partIndex]);

  if (!showPreview || !isClient || !anchorRect) return null;

  const previewWidth = 320;
  const previewTop = anchorRect.top + anchorRect.height / 2;
  const previewLeft = Math.max(16, anchorRect.left - previewWidth - 12);

  return createPortal(
    <div
      className="fixed z-[1000000] -translate-y-1/2 animate-in fade-in duration-200 pointer-events-none"
      style={{
        top: `${previewTop}px`,
        left: `${previewLeft}px`,
        width: `${previewWidth}px`,
      }}
    >
       <Card className="rounded-3xl p-4 bg-black-700 shadow-xl min-w-[300px]">
            <div
              ref={canvasContainerRef}
              className="w-full h-36 bg-gold-300 rounded-2xl mb-3 overflow-hidden relative"
            >
              {isLoading && !previewReady && <div className="absolute inset-0 h-full w-full animate-pulse bg-gold-400" />}
             {!isLoading && previewError && (
               <div className="absolute inset-0 h-full w-full flex items-center justify-center text-xs text-gold-300 px-3 text-center">
                 {previewError}
               </div>
             )}
             {!isLoading && !previewError && !previewReady && (
               <div className="absolute inset-0 h-full w-full flex items-center justify-center text-xs text-gold-300 px-3 text-center">
                Ładowanie podglądu 3D...
              </div>
            )}
          </div>

           {/* Part Details */}
           <div className="space-y-2">
             <h4 className="font-semibold text-gold-300 text-sm line-clamp-2">
             {part.name}
           </h4>

           {/* Quantity Badge */}
             <Badge variant="secondary" className="rounded-full bg-gold-300 text-black-700 text-xs">
              Ilość: ×{part.quantity}
            </Badge>

           {/* Part Type */}
            {part.part_type && (
               <div className="text-xs">
                 <span className="font-medium text-gold-300">Typ:</span>{" "}
                 <span className="text-gold-200">{part.part_type}</span>
               </div>
             )}

          {/* Dimensions */}
            {part.dimensions && (
              <div className="text-xs space-y-1">
                <p className="font-medium text-gold-300">Wymiary:</p>
                <ul className="text-gold-200 pl-3">
                <li>
                  • Szerokość: {part.dimensions.width.toFixed(2)} mm
                </li>
                <li>
                  • Wysokość: {part.dimensions.height.toFixed(2)} mm
                </li>
                <li>
                  • Głębokość: {part.dimensions.depth.toFixed(2)} mm
                </li>
              </ul>
            </div>
          )}

          {/* Volume */}
            {part.volume && (
              <div className="text-xs">
                <span className="font-medium text-gold-300">Objętość:</span>{" "}
                <span className="text-gold-200">
                {part.volume.toFixed(2)} cm³
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>,
    document.body
  );
}
