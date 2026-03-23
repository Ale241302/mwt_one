'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface CreditBarProps {
  used: number;
  total: number;
  currency?: string;
  className?: string;
}

export function CreditBar({ used, total, currency = 'USD', className = '' }: CreditBarProps) {
  const percentage = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  const isWarning = percentage >= 90;

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(val);

  return (
    <div 
      className={`p-4 rounded-xl ${className}`}
      style={{
        background: 'var(--surface-glass-bg)',
        border: '1px solid var(--surface-glass-border)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
      }}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Límite de Crédito ({currency})</span>
        <span className="text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>
          {formatCurrency(used)} / {formatCurrency(total)}
        </span>
      </div>

      <div 
        className="w-full h-2 rounded-full overflow-hidden" 
        style={{ background: 'var(--bg-alt)' }}
      >
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{
            background: isWarning ? 'var(--critical)' : 'var(--success)',
            boxShadow: isWarning ? '0 0 10px var(--pulse-warning)' : 'none',
          }}
        />
      </div>

      {isWarning && (
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ repeat: Infinity, duration: 1, repeatType: 'reverse' }}
          className="text-xs mt-2"
          style={{ color: 'var(--critical)' }}
        >
          Advertencia: Utilización cercana al máximo permitido.
        </motion.p>
      )}
    </div>
  );
}
