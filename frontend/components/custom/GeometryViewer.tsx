"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface GeometryViewerProps {
  glbUrl: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

export function GeometryViewer({
  glbUrl,
  onLoad,
  onError,
}: GeometryViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    if (!containerRef.current || !glbUrl) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    try {
      // Scene setup
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xfdfdfd); // bright_snow-900

      // Camera setup
      const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
      camera.position.set(0, 0, 100);

      // Renderer setup
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(window.devicePixelRatio);
      containerRef.current.appendChild(renderer.domElement);

      // Lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(5, 5, 5);
      scene.add(directionalLight);

      // Simple geometry loader (GLB support via THREE.GLTFLoader)
      // For now, create a placeholder cube
      const geometry = new THREE.BoxGeometry(50, 50, 50);
      const material = new THREE.MeshPhongMaterial({ color: 0xa7a2a9 }); // lilac_ash-500
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate);
        mesh.rotation.x += 0.003;
        mesh.rotation.y += 0.005;
        renderer.render(scene, camera);
      };

      animate();

      // Handle window resize
      const handleResize = () => {
        if (!containerRef.current) return;
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

      // Call onLoad callback
      if (onLoad) onLoad();

      return () => {
        window.removeEventListener("resize", handleResize);
        containerRef.current?.removeChild(renderer.domElement);
        geometry.dispose();
        material.dispose();
        renderer.dispose();
      };
    } catch (error) {
      if (onError && error instanceof Error) {
        onError(error);
      }
    }
  }, [glbUrl, onLoad, onError]);

  return (
    <div
      ref={containerRef}
      className="w-full rounded-3xl bg-bright_snow-600 border border-lilac_ash-200 overflow-hidden"
      style={{ aspectRatio: "1" }}
    />
  );
}
