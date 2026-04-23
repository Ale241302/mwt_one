"""S28-GH-SYNC: Clona/pullea mwt-knowledge-hub y devuelve el diff contra el último SHA sincronizado.

Flujo:
    1. Si /kb/_repo no existe -> clone shallow.
    2. Si existe -> fetch + reset --hard origin/<branch>.
    3. Diff (name-status) entre last_sha (BD) y HEAD actual, restringido a KB_REPO_SUBDIR (docs/).
    4. Copiar .md vigentes a /kb/<subdir>/... (mirror) y borrar los eliminados.
    5. Devolver listas added/modified/deleted (en rutas relativas al mirror) y el nuevo SHA.

Autenticación: GITHUB_TOKEN se inserta en la URL como https://x-access-token:<TOKEN>@github.com/...
Si el repo es público, GITHUB_TOKEN puede quedar vacío.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from sqlalchemy import text

logger = logging.getLogger(__name__)

# --- Config vía env ---
KB_PATH        = Path(os.getenv('KB_PATH', '/kb'))
REPO_DIR       = KB_PATH / '_repo'                                  # clon completo
REPO_URL       = os.getenv('KB_REPO_URL', 'https://github.com/sjoalfaro/mwt-knowledge-hub')
REPO_BRANCH    = os.getenv('KB_REPO_BRANCH', 'main')
REPO_SUBDIR    = os.getenv('KB_REPO_SUBDIR', 'docs').strip('/')     # carpeta dentro del repo que se indexa
GITHUB_TOKEN   = os.getenv('GITHUB_TOKEN', '').strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_url(url: str, token: str) -> str:
    """Inyecta el token en la URL HTTPS del repo (si hay token)."""
    if not token:
        return url
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return url  # no-op para URLs SSH
    netloc = f'x-access-token:{token}@{parsed.hostname}'
    if parsed.port:
        netloc += f':{parsed.port}'
    return urlunparse(parsed._replace(netloc=netloc))


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    """Ejecuta git y devuelve stdout. Lanza RuntimeError si falla."""
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'   # nunca pedir credenciales interactivas
    proc = subprocess.run(
        ['git', *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        # Enmascara el token si aparece en el stderr
        err = proc.stderr.replace(GITHUB_TOKEN, '***') if GITHUB_TOKEN else proc.stderr
        raise RuntimeError(f'git {" ".join(args)} failed ({proc.returncode}): {err.strip()}')
    return proc.stdout


def _ensure_clone() -> None:
    """Clona el repo si REPO_DIR aún no existe (o está vacío/corrupto)."""
    if (REPO_DIR / '.git').is_dir():
        return
    if REPO_DIR.exists():
        shutil.rmtree(REPO_DIR)
    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
    logger.info('Cloning %s (branch %s) into %s', REPO_URL, REPO_BRANCH, REPO_DIR)
    _run_git([
        'clone',
        '--branch', REPO_BRANCH,
        '--single-branch',
        _auth_url(REPO_URL, GITHUB_TOKEN),
        str(REPO_DIR),
    ])


def _fetch_and_reset() -> None:
    """Actualiza el working tree al último commit de origin/<branch>."""
    # Re-set origin con token (en caso de rotar token)
    _run_git(['remote', 'set-url', 'origin', _auth_url(REPO_URL, GITHUB_TOKEN)], cwd=REPO_DIR)
    _run_git(['fetch', 'origin', REPO_BRANCH, '--prune'], cwd=REPO_DIR)
    _run_git(['reset', '--hard', f'origin/{REPO_BRANCH}'], cwd=REPO_DIR)
    _run_git(['clean', '-fdx'], cwd=REPO_DIR)


def _current_sha() -> str:
    return _run_git(['rev-parse', 'HEAD'], cwd=REPO_DIR).strip()


def _load_last_sha(db_conn) -> str | None:
    row = db_conn.execute(text('SELECT last_sha FROM kb_sync_state WHERE id = 1')).fetchone()
    return row[0] if row and row[0] else None


def _save_state(db_conn, *, sha: str, status: str, error: str | None) -> None:
    db_conn.execute(text('''
        UPDATE kb_sync_state
           SET repo_url       = :url,
               branch         = :branch,
               last_sha       = :sha,
               last_synced_at = NOW(),
               last_status    = :status,
               last_error     = :error
         WHERE id = 1
    '''), {
        'url': REPO_URL,
        'branch': REPO_BRANCH,
        'sha': sha,
        'status': status,
        'error': error,
    })


def _subdir_prefix() -> str:
    """Prefijo con '/' al final que filtra rutas del subdir."""
    return f'{REPO_SUBDIR}/' if REPO_SUBDIR else ''


def _is_md(path: str) -> bool:
    return path.lower().endswith('.md')


def _in_subdir(path: str) -> bool:
    prefix = _subdir_prefix()
    return path.startswith(prefix) if prefix else True


def _list_subdir_md_full() -> list[str]:
    """Devuelve todas las rutas .md bajo REPO_SUBDIR (para el primer sync)."""
    base = REPO_DIR / REPO_SUBDIR if REPO_SUBDIR else REPO_DIR
    if not base.exists():
        return []
    return [
        str(p.relative_to(REPO_DIR)).replace(os.sep, '/')
        for p in base.rglob('*.md')
    ]


def _diff_name_status(old_sha: str, new_sha: str) -> list[tuple[str, str, str | None]]:
    """Lista (status, path, old_path) del git diff --name-status <old>..<new>."""
    out = _run_git(
        ['diff', '--name-status', '-M', f'{old_sha}..{new_sha}', '--', _subdir_prefix() or '.'],
        cwd=REPO_DIR,
    )
    results: list[tuple[str, str, str | None]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        status = parts[0]
        if status.startswith('R') and len(parts) >= 3:
            results.append((status[0], parts[2], parts[1]))   # rename: new, old
        else:
            results.append((status[0], parts[1], None))
    return results


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

@dataclass
class SyncDiff:
    new_sha: str
    old_sha: str | None
    added:    list[str] = field(default_factory=list)   # paths relativos al REPO_DIR
    modified: list[str] = field(default_factory=list)
    deleted:  list[str] = field(default_factory=list)
    first_sync: bool = False

    @property
    def upserts(self) -> list[str]:
        return self.added + self.modified

    def as_dict(self) -> dict:
        return {
            'new_sha': self.new_sha,
            'old_sha': self.old_sha,
            'first_sync': self.first_sync,
            'added':    self.added,
            'modified': self.modified,
            'deleted':  self.deleted,
        }


def sync_repo(db_conn) -> SyncDiff:
    """Ejecuta el sync y devuelve el diff de archivos .md bajo REPO_SUBDIR.

    Idempotente: si no hay cambios, retorna listas vacías.
    """
    _ensure_clone()
    _fetch_and_reset()
    new_sha = _current_sha()
    old_sha = _load_last_sha(db_conn)

    diff = SyncDiff(new_sha=new_sha, old_sha=old_sha)

    if old_sha is None:
        # Primer sync: todo cuenta como 'added'
        diff.first_sync = True
        diff.added = [p for p in _list_subdir_md_full() if _is_md(p)]
    elif old_sha == new_sha:
        # Nada que hacer
        pass
    else:
        for status, path, old_path in _diff_name_status(old_sha, new_sha):
            if not _in_subdir(path):
                continue
            if status in ('A',) and _is_md(path):
                diff.added.append(path)
            elif status in ('M',) and _is_md(path):
                diff.modified.append(path)
            elif status == 'D' and _is_md(path):
                diff.deleted.append(path)
            elif status == 'R':
                # rename: borrar el viejo e indexar el nuevo
                if old_path and _is_md(old_path) and _in_subdir(old_path):
                    diff.deleted.append(old_path)
                if _is_md(path):
                    diff.added.append(path)
            elif status == 'T' and _is_md(path):
                diff.modified.append(path)
            # C (copy), U (unmerged), X (unknown) los ignoramos

    return diff


def persist_sync_state(db_conn, *, sha: str, status: str, error: str | None = None) -> None:
    """Actualiza la fila singleton de kb_sync_state. Debe llamarse después del reindex."""
    _save_state(db_conn, sha=sha, status=status, error=error)


def resolve_repo_file(rel_path: str) -> Path:
    """Devuelve la ruta absoluta en /kb/_repo para una ruta relativa del repo."""
    return REPO_DIR / rel_path
