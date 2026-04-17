'use client';

import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls } from '@react-three/drei';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Canvas3DProps {
  geometry: { vertices: number[][]; normals: number[][]; indices: number[] } | null;
}

function Model({ geometry }: { geometry: any }) {
  if (!geometry) return null;

  const meshRef = useRef<THREE.Mesh>(null);

  useEffect(() => {
    if (meshRef.current && geometry) {
      const bufferGeometry = new THREE.BufferGeometry();

      // Convert vertices and indices
      const vertices = new Float32Array(geometry.vertices.flat());
      const indices = new Uint32Array(geometry.indices);
      const normals = new Float32Array(geometry.normals.flat());

      bufferGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      bufferGeometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
      bufferGeometry.setIndex(new THREE.BufferAttribute(indices, 1));

      meshRef.current.geometry = bufferGeometry;
    }
  }, [geometry]);

  return (
    <mesh ref={meshRef} castShadow receiveShadow>
      <meshPhongMaterial color="#66666e" />
    </mesh>
  );
}

export function Canvas3D({ geometry }: Canvas3DProps) {
  return (
    <Canvas camera={{ position: [0, 0, 100], far: 10000 }} shadows>
      <PerspectiveCamera makeDefault position={[50, 50, 50]} />
      <OrbitControls
        enableZoom={true}
        enablePan={true}
        enableRotate={true}
        autoRotate={false}
      />

      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[100, 100, 50]} intensity={0.8} castShadow />
      <directionalLight position={[-100, -100, -50]} intensity={0.3} />

      {/* Model */}
      <Model geometry={geometry} />

      {/* Grid */}
      <gridHelper args={[200, 20]} position={[0, -50, 0]} />
    </Canvas>
  );
}
