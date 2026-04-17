'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/upload');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-platinum">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
        <p className="text-dim-grey">Ładowanie...</p>
      </div>
    </div>
  );
}
