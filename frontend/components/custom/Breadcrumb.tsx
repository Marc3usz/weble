"use client";

import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  currentPage: string;
}

/**
 * Text-based breadcrumb navigation component
 * Shows navigation path: Upload > Model XYZ > Części
 * 
 * Each step is clickable and preserves model state via app store
 * Current page is shown but not clickable
 */
export function Breadcrumb({ items, currentPage }: BreadcrumbProps) {
  return (
    <nav className="flex items-center gap-2 px-4 py-3 bg-bright_snow-900 rounded-3xl border border-lilac_ash-100">
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {/* Breadcrumb Item */}
          {item.href ? (
            <Link
              href={item.href}
              className={cn(
                "text-charcoal-500 hover:text-lilac_ash-500",
                "transition-colors duration-200",
                "hover:border-b-2 hover:border-lilac_ash-500",
                "pb-1"
              )}
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-charcoal-500">{item.label}</span>
          )}

          {/* Separator (only if not last item) */}
          {index < items.length - 1 && (
            <span className="text-charcoal-400 mx-1">›</span>
          )}
        </React.Fragment>
      ))}

      {/* Current Page (non-clickable, highlighted) */}
      <span className="text-charcoal-400 mx-1">›</span>
      <span className={cn(
        "text-lilac_ash-500 font-semibold",
        "border-b-2 border-lilac_ash-500",
        "pb-1"
      )}>
        {currentPage}
      </span>
    </nav>
  );
}
