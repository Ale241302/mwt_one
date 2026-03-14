/**
 * S9-16 Fix 4 — Card global MWT ONE
 * Uso: <Card>contenido</Card>
 *      <Card padding="sm" shadow="md">...</Card>
 */
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  shadow?: "none" | "sm" | "md" | "lg";
  /** Si true, elimina el borde */
  noBorder?: boolean;
  /** Permite sobrescribir el border-radius */
  radius?: "md" | "lg" | "xl" | "2xl";
  as?: keyof JSX.IntrinsicElements;
}

const PADDING_CLASSES: Record<NonNullable<CardProps["padding"]>, string> = {
  none: "",
  sm:   "p-4",
  md:   "p-6",
  lg:   "p-8",
};

const SHADOW_CLASSES: Record<NonNullable<CardProps["shadow"]>, string> = {
  none: "",
  sm:   "shadow-[var(--shadow-sm)]",
  md:   "shadow-[var(--shadow-md)]",
  lg:   "shadow-[var(--shadow-lg)]",
};

const RADIUS_CLASSES: Record<NonNullable<CardProps["radius"]>, string> = {
  md:  "rounded-lg",
  lg:  "rounded-xl",
  xl:  "rounded-[var(--radius-xl)]",
  "2xl": "rounded-[var(--radius-2xl)]",
};

export function Card({
  children,
  className,
  padding = "md",
  shadow = "sm",
  noBorder = false,
  radius = "xl",
  as: Tag = "div",
}: CardProps) {
  return (
    <Tag
      className={cn(
        "bg-[var(--surface)]",
        RADIUS_CLASSES[radius],
        SHADOW_CLASSES[shadow],
        !noBorder && "border border-[var(--border)]",
        PADDING_CLASSES[padding],
        className
      )}
    >
      {children}
    </Tag>
  );
}

/** Sub-componente: header de card con border-b */
export function CardHeader({
  children,
  className,
}: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "px-6 py-4 border-b border-[var(--border)] font-semibold text-[var(--text-primary)]",
        className
      )}
    >
      {children}
    </div>
  );
}

/** Sub-componente: footer de card con border-t */
export function CardFooter({
  children,
  className,
}: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "px-6 py-4 border-t border-[var(--border)] flex items-center justify-end gap-2",
        className
      )}
    >
      {children}
    </div>
  );
}
