"use client";

import { useState, useEffect, useCallback } from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import api from '@/lib/api';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface Document {
  artifact_id: string;
  artifact_type: string;
  label: string;
  status: string;
  has_file: boolean;
  file_url: string | null;
  filename: string;
  created_at: string;
  // alias de compatibilidad por si el backend añade campos extras
  id?: string;
  name?: string;
}

interface DocumentMirrorPanelProps {
  expedienteId: string;
}

/** Extrae el array de documentos desde cualquier forma del response:
 *  - { count, documents: [...] }   → nuevo endpoint /documents/
 *  - { results: [...] }            → DRF pagination
 *  - [...]                         → array plano
 *  - cualquier otra cosa           → []
 */
function extractDocuments(data: unknown): Document[] {
  if (Array.isArray(data)) return data as Document[];
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>;
    if (Array.isArray(d.documents)) return d.documents as Document[];
    if (Array.isArray(d.results)) return d.results as Document[];
  }
  return [];
}

export default function DocumentMirrorPanel({ expedienteId }: DocumentMirrorPanelProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`expedientes/${expedienteId}/documents/`);
      // ✅ Siempre array, sin importar el envelope
      setDocuments(extractDocuments(res.data));
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  // Usamos artifact_id como key primaria; si viene id también funciona
  const keyOf = (doc: Document) => doc.artifact_id ?? doc.id ?? doc.filename;
  const nameOf = (doc: Document) => doc.label ?? doc.name ?? doc.filename;

  return (
    <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <FileText className="w-4 h-4 text-text-secondary" />
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
          Documentos
        </h2>
        {!loading && (
          <span className="px-2 py-0.5 bg-border text-text-secondary text-xs font-semibold rounded-full">
            {documents.length}
          </span>
        )}
      </div>

      {/* Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-border rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && documents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-text-tertiary">
          <FileText className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm">No hay documentos adjuntos aún</p>
          <p className="text-xs mt-1">Los archivos PDF de los artefactos aparecerán aquí</p>
        </div>
      )}

      {/* Document grid */}
      {!loading && documents.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {documents.map(doc => (
            <div
              key={keyOf(doc)}
              className="flex items-center gap-3 p-3 bg-bg-alt border border-border rounded-xl hover:border-navy/40 transition-colors group"
            >
              <div className="flex-shrink-0 w-9 h-9 bg-red-50 border border-red-200 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-red-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{nameOf(doc)}</p>
                <p className="text-xs text-text-tertiary">
                  {doc.artifact_type && <span className="mr-1.5">{doc.artifact_type}</span>}
                  {doc.created_at
                    ? format(new Date(doc.created_at), 'd MMM yyyy', { locale: es })
                    : ''}
                </p>
              </div>
              {doc.has_file && doc.file_url ? (
                <a
                  href={doc.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 p-1.5 rounded-lg text-text-tertiary hover:text-navy hover:bg-navy/10 transition-colors"
                  title="Ver documento"
                >
                  <ExternalLink size={14} />
                </a>
              ) : (
                <span className="flex-shrink-0 p-1.5 text-text-tertiary opacity-30" title="Sin archivo adjunto">
                  <ExternalLink size={14} />
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
