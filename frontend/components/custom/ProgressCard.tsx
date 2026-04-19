import React from "react";
import { Card } from "@/components/ui/card";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProgressCardProps {
  icon: React.ReactNode;
  title: string;
  status: "pending" | "processing" | "completed" | "failed";
  details?: string;
  isLoading?: boolean;
}

export function ProgressCard({
  icon,
  title,
  status,
  details,
  isLoading = false,
}: ProgressCardProps) {
  const getStatusIcon = () => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-lilac_ash-500" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case "processing":
        return (
          <Clock className="w-5 h-5 text-lilac_ash-500 animate-spin" />
        );
      case "pending":
      default:
        return <Clock className="w-5 h-5 text-charcoal-400" />;
    }
  };

  const getBackgroundColor = () => {
    if (status === "completed") return "bg-lilac_ash-50 border-lilac_ash-200";
    if (status === "failed") return "bg-red-50 border-red-200";
    return "bg-bright_snow-600 border-lilac_ash-200";
  };

  const getTitleColor = () => {
    if (status === "completed") return "text-lilac_ash-600";
    if (status === "failed") return "text-red-600";
    return "text-black-DEFAULT";
  };

  return (
    <Card
      className={cn(
        "rounded-3xl p-6 border transition-all duration-500",
        getBackgroundColor(),
        isLoading && "animate-pulse"
      )}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={cn("mt-1", status === "completed" && "text-lilac_ash-500")}>
          {icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={cn("font-semibold", getTitleColor())}>
              {title}
            </h3>
            {getStatusIcon()}
          </div>

          {details && (
            <p className="text-sm text-charcoal-500 mt-1 truncate">
              {details}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
