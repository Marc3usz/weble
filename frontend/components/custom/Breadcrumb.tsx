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
  actions?: React.ReactNode;
}

/**
 * Text-based breadcrumb navigation component
 * Shows navigation path: Upload > Model XYZ > Części
 * 
 * Each step is clickable and preserves model state via app store
 * Current page is shown but not clickable
 */
export function Breadcrumb({ items, currentPage, actions }: BreadcrumbProps) {
  return (
    <nav className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-lilac_ash-300 rounded-3xl">
      <div className="flex flex-wrap items-center gap-2">
        {items.map((item, index) => (
          <React.Fragment key={index}>
            {item.href ? (
              <Link
                href={item.href}
                className={cn(
                  "text-charcoal-700 hover:text-black-DEFAULT",
                  "transition-colors duration-200",
                  "px-2 py-1 rounded-xl hover:bg-lilac_ash-500/20 text-sm"
                )}
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-charcoal-700 px-2 py-1 text-sm">{item.label}</span>
            )}

            {index < items.length - 1 && (
              <span className="text-charcoal-600">›</span>
            )}
          </React.Fragment>
        ))}

        <span className="text-charcoal-600">›</span>
        <span className={cn(
          "text-black-DEFAULT font-semibold text-sm",
          "bg-bright_snow-900 rounded-xl px-2 py-1"
        )}>
          {currentPage}
        </span>
      </div>

      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </nav>
  );
}
