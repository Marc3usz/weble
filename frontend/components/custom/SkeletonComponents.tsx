import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface SkeletonCardProps {
  width?: string;
  height?: string;
  className?: string;
  animated?: boolean;
}

export function SkeletonCard({
  width = "w-full",
  height = "h-24",
  className,
  animated = true,
}: SkeletonCardProps) {
  return (
    <Skeleton
      className={cn(
        width,
        height,
        "rounded-3xl",
        animated && "animate-pulse",
        className
      )}
    />
  );
}

interface ProgressCardSkeletonProps {
  count?: number;
}

export function ProgressCardsSkeleton({ count = 3 }: ProgressCardSkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-3xl p-6 bg-bright_snow-600 border border-lilac_ash-200 space-y-3"
        >
          <div className="flex items-center gap-3">
            <Skeleton className="w-6 h-6 rounded-full animate-pulse" />
            <Skeleton className="w-32 h-4 rounded-full animate-pulse" />
          </div>
          <Skeleton className="w-48 h-3 rounded-full animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export function GeometryViewerSkeleton() {
  return (
    <div className="w-full rounded-3xl bg-bright_snow-600 border border-lilac_ash-200 aspect-square animate-pulse" />
  );
}

export function StepCarouselSkeleton() {
  return (
    <div className="space-y-6">
      {/* Step image */}
      <Skeleton className="w-full h-96 rounded-3xl animate-pulse" />

      {/* Step info */}
      <div className="space-y-3">
        <Skeleton className="w-32 h-4 rounded-full animate-pulse" />
        <Skeleton className="w-full h-3 rounded-full animate-pulse" />
        <Skeleton className="w-full h-3 rounded-full animate-pulse" />
        <Skeleton className="w-2/3 h-3 rounded-full animate-pulse" />
      </div>
    </div>
  );
}

export function PartGridSkeleton() {
  return (
    <div className="grid grid-cols-3 gap-6">
      {Array.from({ length: 9 }).map((_, i) => (
        <div
          key={i}
          className="rounded-3xl p-6 bg-bright_snow-600 border border-lilac_ash-200 space-y-4"
        >
          <Skeleton className="w-full h-24 rounded-2xl animate-pulse" />
          <Skeleton className="w-full h-4 rounded-full animate-pulse" />
          <Skeleton className="w-2/3 h-3 rounded-full animate-pulse" />
        </div>
      ))}
    </div>
  );
}
