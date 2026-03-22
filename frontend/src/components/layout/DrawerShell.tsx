"use client";

import { ReactNode } from 'react';
import { X } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface DrawerShellProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  loading?: boolean;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl';
}

const widthClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
};

export default function DrawerShell({
  open,
  onClose,
  title,
  children,
  footer,
  loading = false,
  maxWidth = 'md',
}: DrawerShellProps) {
  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/40 z-[60] backdrop-blur-[1px] transition-opacity" 
        aria-hidden="true" 
        onClick={() => !loading && onClose()} 
      />

      {/* Drawer */}
      <div 
        className={cn(
          "fixed inset-y-0 right-0 w-full bg-surface shadow-2xl z-[70] flex flex-col transition-transform duration-300 ease-in-out",
          widthClasses[maxWidth]
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-shell-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-alt/30">
          <h3 id="drawer-shell-title" className="text-base font-bold text-text-primary uppercase tracking-tight">
            {title}
          </h3>
          <button 
            onClick={onClose} 
            disabled={loading} 
            className="text-text-tertiary hover:text-text-primary p-2 rounded-full hover:bg-bg-alt transition-colors focus:outline-none focus:ring-2 focus:ring-navy/20"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-6 py-5 border-t border-border bg-bg-alt/20">
            {footer}
          </div>
        )}

        {/* Loading Overlay (Internal) */}
        {loading && (
          <div className="absolute inset-0 bg-white/10 z-[80] flex items-center justify-center cursor-wait backdrop-blur-[0.5px]">
            <div className="w-8 h-8 border-3 border-navy border-t-transparent rounded-full animate-spin shadow-sm" />
          </div>
        )}
      </div>
    </>
  );
}
