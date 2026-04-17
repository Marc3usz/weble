import React, { useEffect, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import * as THREE from 'three';
import { Geometry } from '@/app/types';

interface GeometryViewerProps {
  geometry: Geometry | undefined;
}

// Geometry Mesh Component
function GeometryMesh({ geometry }: { geometry: Geometry }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useEffect(() => {
    if (!meshRef.current || !geometry) return;

    // Create BufferGeometry from vertices, normals, and indices
    const bufferGeometry = new THREE.BufferGeometry();

    // Convert vertices to Float32Array
    const vertices = new Float32Array(geometry.vertices.flat());
    bufferGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

    // Add normals if available
    if (geometry.normals && geometry.normals.length > 0) {
      const normals = new Float32Array(geometry.normals.flat());
      bufferGeometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
    } else {
      bufferGeometry.computeVertexNormals();
    }

    // Add indices if available
    if (geometry.indices && geometry.indices.length > 0) {
      const indices = new Uint32Array(geometry.indices);
      bufferGeometry.setIndex(new THREE.BufferAttribute(indices, 1));
    }

    bufferGeometry.computeBoundingBox();

    // Assign the geometry
    meshRef.current.geometry.dispose();
    meshRef.current.geometry = bufferGeometry;
  }, [geometry]);

  return (
    <mesh ref={meshRef}>
      <meshStandardMaterial color="#2563eb" metalness={0.3} roughness={0.7} />
    </mesh>
  );
}

// Camera Control Component
function CameraController() {
  const { camera, scene } = useThree();

  useEffect(() => {
    if (scene.children.length === 0) return;

    // Calculate bounding box
    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    
    // Ensure camera is PerspectiveCamera for fov calculation
    let cameraZ = 150;
    if (camera instanceof THREE.PerspectiveCamera) {
      const fov = camera.fov * (Math.PI / 180);
      cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
    }

    // IKEA-style view: left-front with slight top angle
    // Direction: (-1, -2, 0.5) normalized
    const direction = new THREE.Vector3(-1, -2, 0.5).normalize();
    const center = box.getCenter(new THREE.Vector3());

    camera.position.copy(center.clone().add(direction.multiplyScalar(cameraZ * 1.5)));
    camera.lookAt(center);
    camera.updateProjectionMatrix();
  }, [camera, scene]);

  return null;
}

// Canvas Component
function GeometryCanvas({ geometry }: { geometry: Geometry }) {
  return (
    <Canvas
      camera={{ position: [100, 100, 100], fov: 50 }}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Lights */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 20, 10]} intensity={0.8} />
      <directionalLight position={[-10, -10, -10]} intensity={0.3} />

      {/* Grid */}
      <Grid args={[200, 200]} cellSize={10} cellColor="#e2e8f0" sectionSize={100} sectionColor="#cbd5e1" />

      {/* Geometry */}
      <GeometryMesh geometry={geometry} />

      {/* Camera Control */}
      <CameraController />

      {/* Orbit Controls */}
      <OrbitControls />
    </Canvas>
  );
}

export default function GeometryViewer({ geometry }: GeometryViewerProps) {
  if (!geometry) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-100">
        <p className="text-slate-600">Wczytywanie modelu 3D...</p>
      </div>
    );
  }

  return <GeometryCanvas geometry={geometry} />;
}
