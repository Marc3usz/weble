import React from "react";
import { ProgressPageContent } from "@/components/custom/ProgressPageContent";

interface ProgressPageProps {
  params: Promise<{
    jobId: string;
  }>;
  searchParams: Promise<{
    modelId?: string;
  }>;
}

export default async function ProgressPage({
  params,
  searchParams,
}: ProgressPageProps) {
  const resolvedParams = await params;
  const resolvedSearchParams = await searchParams;

  return (
    <ProgressPageContent
      jobId={resolvedParams.jobId}
      modelId={resolvedSearchParams.modelId || null}
    />
  );
}
