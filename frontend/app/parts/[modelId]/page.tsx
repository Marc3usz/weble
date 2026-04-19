import React from "react";
import { PartsPageContent } from "@/components/custom/PartsPageContent";

interface PartsPageProps {
  params: Promise<{
    modelId: string;
  }>;
}

export default async function PartsPage({ params }: PartsPageProps) {
  const resolvedParams = await params;
  return <PartsPageContent modelId={resolvedParams.modelId} />;
}
