import React from "react";
import { ModelPageContent } from "@/components/custom/ModelPageContent";

interface ModelPageProps {
  params: Promise<{
    modelId: string;
  }>;
}

export default async function ModelPage({ params }: ModelPageProps) {
  const resolvedParams = await params;
  return <ModelPageContent modelId={resolvedParams.modelId} />;
}
