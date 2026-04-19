import React from "react";
import { AssemblyPageContent } from "@/components/custom/AssemblyPageContent";

interface AssemblyPageProps {
  params: Promise<{
    modelId: string;
  }>;
}

export default async function AssemblyPage({ params }: AssemblyPageProps) {
  const resolvedParams = await params;
  return <AssemblyPageContent modelId={resolvedParams.modelId} />;
}
