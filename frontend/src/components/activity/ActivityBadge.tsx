"use client";

import React from 'react';
import { Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActivityBadgeProps {
  count: number;
  onClick: () => void;
  className?: string;
}

export default function ActivityBadge({ count, onClick, className }: ActivityBadgeProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative p-2 rounded-full transition-all duration-200 hover:bg-surface active:scale-95 group",
        className
      )}
      aria-label="Activity Feed"
    >
      <Bell 
        className={cn(
          "w-5 h-5 transition-colors",
          count > 0 ? "text-mint fill-mint/10" : "text-text-secondary group-hover:text-text-primary"
        )} 
      />
      
      {count > 0 && (
        <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-bg animate-in zoom-in duration-300">
          {count > 99 ? '99+' : count}
        </span>
      )}
    </button>
  );
}
