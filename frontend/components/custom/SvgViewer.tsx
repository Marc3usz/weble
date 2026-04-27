"use client";

import React, { useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SvgViewerProps {
  svgContent: string;
  title?: string;
  triggerLabel?: string;
}

export function SvgViewer({
  svgContent,
  title = "Diagram",
  triggerLabel = "View Diagram",
}: SvgViewerProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!svgContent) {
    return null;
  }

  return (
    <>
      {/* Trigger Button */}
       <Button
         onClick={() => setIsOpen(true)}
         className="px-4 py-2 bg-gold-500 hover:bg-gold-600 text-black-900 font-medium rounded-2xl transition-colors"
       >
        {triggerLabel}
      </Button>

      {/* Modal Lightbox */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
             {/* Header */}
             <div className="flex items-center justify-between p-6 border-b border-gold-400">
               <h2 className="text-xl font-bold text-gold-200">{title}</h2>
               <button
                 onClick={() => setIsOpen(false)}
                 className="p-2 hover:bg-gold-100 rounded-full transition-colors"
               >
                 <X className="w-5 h-5 text-black-600" />
               </button>
             </div>

             {/* Content */}
             <div className="p-6 flex items-center justify-center bg-black-600">
               <div
                 className="w-full"
                 dangerouslySetInnerHTML={{ __html: svgContent }}
               />
             </div>

             {/* Footer */}
             <div className="p-4 border-t border-gold-400 flex justify-end">
               <Button
                 onClick={() => setIsOpen(false)}
                 className="px-6 py-2 bg-gold-500 hover:bg-gold-600 text-black-900 font-medium rounded-2xl transition-colors"
               >
                Zamknij
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
