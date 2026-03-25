"""S16-07: load_knowledge management command.

Carga archivos de la carpeta knowledge/ al vector store (pgvector).
Excluye archivos CEO-ONLY y secciones marcadas con ceo_only_sections en el YAML front matter.
Excluye prefijos de sprint/documentación interna.

Uso:
    python manage.py load_knowledge                    # carga todos los archivos elegibles
    python manage.py load_knowledge --dry-run          # muestra qué haría sin persistir
    python manage.py load_knowledge --file path/to/file.md  # carga un solo archivo
    python manage.py load_knowledge --dir /custom/path  # carga desde directorio custom
"""
import os
import logging
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

# Prefijos de archivo a excluir (no van al knowledge store)
EXCLUDED_PREFIXES = [
    'LOTE_SM_SPRINT',
    'REPORTE_',
    'PATCH_',
    'MANIFIESTO_APPEND_',
    'CHECKPOINT_SESSION_',
    'GUIA_ALE_',
    'PROMPT_ANTIGRAVITY_',
    'PROMPT_',
    'RESUMEN_SPRINT',
]

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'.md', '.txt', '.rst'}


def _should_exclude_file(filename: str) -> bool:
    """Retorna True si el archivo debe ser excluido por prefijo."""
    basename = Path(filename).name
    return any(basename.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def parse_visibility(filepath: str):
    """Parsea el front matter YAML y retorna (should_include, ceo_only_section_ids).

    Returns:
        (False, []) si el archivo completo es CEO-ONLY (excluir todo).
        (True, [section_ids]) si solo algunas secciones son CEO-ONLY.
    """
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except Exception as exc:
        logger.warning(f'No se pudo leer {filepath}: {exc}')
        return True, []

    front_matter = {}
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            try:
                front_matter = yaml.safe_load(content[3:end]) or {}
            except yaml.YAMLError:
                front_matter = {}

    visibility = front_matter.get('visibility', '[INTERNAL]')
    if 'CEO-ONLY' in str(visibility):
        return False, []

    ceo_only_sections = front_matter.get('ceo_only_sections', [])
    return True, ceo_only_sections


def split_by_headings(content: str, ceo_only_sections: list) -> list:
    """Divide el contenido en chunks por heading ##, excluyendo secciones CEO-ONLY.

    Returns:
        Lista de strings con el contenido de cada chunk no-CEO-ONLY.
    """
    chunks = []
    current_section_id = None
    current_content = []
    skip_current_section = False

    for line in content.split('\n'):
        if line.startswith('## '):
            # Guardar sección anterior si no es CEO-ONLY
            if current_content and not skip_current_section:
                chunks.append('\n'.join(current_content))

            # Determinar si la nueva sección es CEO-ONLY
            parts = line.split(' ', 2)
            current_section_id = parts[1] if len(parts) > 1 else None
            skip_current_section = (
                current_section_id is not None and
                current_section_id in ceo_only_sections
            )
            current_content = [line]

        elif line.startswith('### '):
            # Verificar si subsección es CEO-ONLY
            parts = line.split(' ', 2)
            sub_id = parts[1] if len(parts) > 1 else None
            if sub_id and any(sub_id.startswith(s) for s in ceo_only_sections):
                continue
            if not skip_current_section:
                current_content.append(line)
        else:
            if not skip_current_section:
                current_content.append(line)

    # Guardar última sección
    if current_content and not skip_current_section:
        chunks.append('\n'.join(current_content))

    return [c for c in chunks if c.strip()]


class Command(BaseCommand):
    help = 'S16-07: Carga archivos de knowledge/ a pgvector, excluyendo CEO-ONLY y sprints internos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué archivos se cargarían sin persistir nada.',
        )
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Ruta a un archivo específico para cargar.',
        )
        parser.add_argument(
            '--dir',
            type=str,
            default=None,
            help='Directorio desde donde cargar (default: settings.KNOWLEDGE_DIR o ../knowledge/)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_file = options.get('file')
        custom_dir = options.get('dir')

        # Determinar directorio de knowledge
        if custom_dir:
            knowledge_dir = Path(custom_dir)
        else:
            knowledge_dir = Path(
                getattr(settings, 'KNOWLEDGE_DIR', None) or
                Path(settings.BASE_DIR).parent / 'knowledge'
            )

        if not knowledge_dir.exists():
            self.stderr.write(
                self.style.ERROR(f'Directorio knowledge no encontrado: {knowledge_dir}')
            )
            return

        # Recopilar archivos
        if specific_file:
            files = [Path(specific_file)]
        else:
            files = [
                p for p in knowledge_dir.rglob('*')
                if p.is_file() and p.suffix in ALLOWED_EXTENSIONS
            ]

        # Filtrar
        eligible = []
        excluded = []
        for f in files:
            if _should_exclude_file(f.name):
                excluded.append(f)
                continue
            should_include, ceo_only = parse_visibility(str(f))
            if not should_include:
                excluded.append(f)
                continue
            eligible.append((f, ceo_only))

        self.stdout.write(f'Total archivos encontrados: {len(files)}')
        self.stdout.write(f'Excluidos (prefijo/CEO-ONLY): {len(excluded)}')
        self.stdout.write(f'Elegibles para carga: {len(eligible)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN — sin persistencia ---'))
            for f, ceo_only in eligible:
                self.stdout.write(f'  ✓ {f.name}')
                if ceo_only:
                    self.stdout.write(f'    Secciones CEO-ONLY excluidas: {ceo_only}')
            self.stdout.write(self.style.WARNING(f'DRY RUN completado. {len(eligible)} archivos serían cargados.'))
            return

        # Cargar al vector store
        loaded_count = 0
        chunk_count = 0
        errors = []

        for filepath, ceo_only_sections in eligible:
            try:
                content = filepath.read_text(encoding='utf-8')

                # Remover front matter YAML
                if content.startswith('---'):
                    end = content.find('---', 3)
                    if end != -1:
                        content = content[end + 3:]

                chunks = split_by_headings(content, ceo_only_sections)
                if not chunks:
                    chunks = [content.strip()]

                # Intentar cargar al vector store (pgvector)
                # TODO: CEO_INPUT_REQUIRED — confirmar la configuración del embedding model
                self._load_chunks_to_vector_store(filepath, chunks)

                loaded_count += 1
                chunk_count += len(chunks)
                self.stdout.write(f'  ✓ {filepath.name} ({len(chunks)} chunks)')

            except Exception as exc:
                error_msg = f'ERROR en {filepath.name}: {exc}'
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                self.stderr.write(self.style.ERROR(error_msg))

        self.stdout.write(self.style.SUCCESS(
            f'Completado: {loaded_count} archivos, {chunk_count} chunks cargados. '
            f'Errores: {len(errors)}'
        ))

    def _load_chunks_to_vector_store(self, filepath, chunks):
        """Carga chunks al vector store interno del knowledge service.

        Llama al endpoint interno del mwt-knowledge service.
        """
        import json
        import urllib.request
        from django.conf import settings

        knowledge_url = getattr(settings, 'KNOWLEDGE_SERVICE_URL', 'http://mwt-knowledge:8001')
        internal_token = getattr(settings, 'KNOWLEDGE_INTERNAL_TOKEN', '')

        documents = [
            {
                'content': chunk,
                'metadata': {
                    'source': str(filepath.name),
                    'filepath': str(filepath),
                    'chunk_index': i,
                }
            }
            for i, chunk in enumerate(chunks)
        ]

        payload = json.dumps({'documents': documents}).encode('utf-8')
        req = urllib.request.Request(
            f'{knowledge_url}/internal/load/',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Internal-Token': internal_token,
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
