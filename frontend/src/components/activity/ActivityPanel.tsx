"use client";

import React from 'react';
import DrawerShell from '@/components/layout/DrawerShell';
import { ActivityEvent } from '@/hooks/useActivityFeed';
import { Clock, User, FileText, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActivityPanelProps {
  isOpen: boolean;
  onClose: () => void;
  events: ActivityEvent[];
  loading: boolean;
  onMarkSeen: () => void;
}

export default function ActivityPanel({
  isOpen,
  onClose,
  events,
  loading,
  onMarkSeen,
}: ActivityPanelProps) {
  
  // Mark as seen when opening the drawer
  React.useEffect(() => {
    if (isOpen) {
      onMarkSeen();
    }
  }, [isOpen, onMarkSeen]);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.RelativeTimeFormat('es', { numeric: 'auto' }).format(
      Math.ceil((date.getTime() - Date.now()) / (1000 * 60)), 
      'minute'
    );
  };

  const getActionLabel = (event: ActivityEvent) => {
    switch (event.event_type) {
      case 'status_changed':
        return `Cambió estado de ${event.previous_status || 'Inicio'} a ${event.new_status}`;
      case 'created':
        return 'Creó el expediente';
      case 'updated':
        return 'Actualizó información';
      case 'comment_added':
        return 'Agregó un comentario';
      default:
        return event.event_type.replace('_', ' ');
    }
  };

  return (
    <DrawerShell
      open={isOpen}
      onClose={onClose}
      title="Monitor de Actividad"
      maxWidth="md"
    >
      <div className="space-y-4">
        {loading && events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 space-y-4 text-text-tertiary">
            <div className="w-8 h-8 border-2 border-mint border-t-transparent rounded-full animate-spin" />
            <p>Cargando actividad...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12 text-text-tertiary italic">
            No hay actividad reciente.
          </div>
        ) : (
          events.map((event) => (
            <div 
              key={event.event_id} 
              className="group relative bg-bg-alt/20 hover:bg-bg-alt/40 border border-border/50 rounded-xl p-4 transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-surface rounded-lg text-mint shadow-sm">
                  <ActivityIcon type={event.event_type} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-xs font-semibold text-mint uppercase tracking-wider">
                      {event.action_source}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-text-tertiary">
                      <Clock size={10} />
                      {new Date(event.occurred_at).toLocaleString('es-CR', { 
                        hour: '2-digit', 
                        minute: '2-digit',
                        day: '2-digit',
                        month: 'short'
                      })}
                    </span>
                  </div>
                  
                  <p className="text-sm text-text-primary font-medium mb-1 line-clamp-2">
                    {getActionLabel(event)}
                  </p>
                  
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 pt-2 border-t border-border/30">
                    <div className="flex items-center gap-1.5 text-xs text-text-secondary">
                      <User size={12} className="text-navy/60" />
                      {event.user_display}
                    </div>
                    
                    {event.expediente_number && (
                      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
                        <FileText size={12} className="text-navy/60" />
                        {event.expediente_number}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="self-center text-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight size={16} />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </DrawerShell>
  );
}

function ActivityIcon({ type }: { type: string }) {
  if (type === 'status_changed') return <Clock size={16} />;
  if (type === 'created') return <FileText size={16} />;
  return <Clock size={16} />;
}
