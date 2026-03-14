/**
 * S9-16 Fix 3 — Badge global MWT ONE
 * Uso: <Badge variant="success">Activo</Badge>
 */
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export type BadgeVariant =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral"
  | "navy"
  | "mint";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: "bg-[#F0FAF6] text-[#0E8A6D]",
  warning: "bg-[#FFF7ED] text-[#B45309]",
  danger:  "bg-[#FEF2F2] text-[#DC2626]",
  info:    "bg-[#EFF6FF] text-[#1D4ED8]",
  neutral: "bg-[#F1F5F9] text-[#475569]",
  navy:    "bg-[#013A57] text-white",
  mint:    "bg-[#E6F7F3] text-[#0E8A6D]",
};

interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: ReactNode;
  icon?: ReactNode;
}

export function Badge({
  variant = "neutral",
  className,
  children,
  icon,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-md",
        "text-[11px] font-semibold uppercase tracking-[0.5px]",
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}
