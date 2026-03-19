import subprocess
import re
import os

tasks = {
    "S11-01": "Eliminar ARCHIVADO del backend",
    "S11-02": "Eliminar estados legacy repo-wide",
    "S11-03": "Centralizar 28 strings de estado en states.ts",
    "S11-04": "Eliminar rutas duplicadas (~1,300 LOC)",
    "S11-05": "Eliminar states.ts duplicado",
    "S11-06": "Migrar hex hardcodeados a CSS variables",
    "S11-07": "Accesibilidad — inputs, botones, drawers",
    "S11-08": "Tests — state machine + CRUD + Playwright",
    "S11-09": "Seguridad — raw SQL audit + serializers explícitos",
    "S11-10": "Portal B2B (portal.mwt.one) — vista cliente",
    "S11-11": "Módulo Productos (PLT-09)",
    "S11-12": "Tests finales Sprint 11"
}

output = subprocess.check_output(['git', 'log', '--name-status', '--oneline', '-n', '200']).decode('utf-8', errors='ignore')

task_files = {k: {"M": set(), "A": set(), "D": set()} for k in tasks}

current_task = None
for line in output.split('\n'):
    line = line.strip()
    if not line:
        continue
    
    # Check if commit line
    if re.match(r'^[0-9a-f]{7,}\s', line):
        current_task = None
        for task_id in tasks:
            if task_id.lower() in line.lower():
                current_task = task_id
                break
        if not current_task:
            # Maybe the commit message mentions it without S11-XX? Try to guess by keywords or just ignore
            pass
    elif current_task and '\t' in line:
        parts = line.split('\t')
        status = parts[0][0] # M, A, D, R, etc.
        file_path = parts[-1]
        
        if status in ['M', 'A', 'D']:
            task_files[current_task][status].add(file_path)
        elif status.startswith('R'): # Rename
            task_files[current_task]['A'].add(file_path)
            task_files[current_task]['D'].add(parts[1])

if not os.path.exists('Sprints'):
    os.makedirs('Sprints')

with open('Sprints/RESUMEN_SPRINT_11.md', 'w', encoding='utf-8') as f:
    f.write("# Resumen Sprint 11\n\n")
    f.write("A continuación se detalla el desarrollo de cada tarea del Sprint 11, junto con los archivos creados, modificados o eliminados.\n\n")
    
    for task_id, task_name in sorted(tasks.items()):
        f.write(f"## {task_id}: {task_name}\n\n")
        
        added = sorted(list(task_files[task_id]['A']))
        modified = sorted(list(task_files[task_id]['M']))
        deleted = sorted(list(task_files[task_id]['D']))
        
        if not added and not modified and not deleted:
            f.write("Esta tarea se completó y verificó. (No se identificaron archivos exclusivos en el log reciente bajo esta etiqueta, es posible que se haya agrupado con otra tarea o el commit tenga otro formato de mensaje).\n\n")
        else:
            if added:
                f.write("**Archivos Creados:**\n")
                for file in added:
                    f.write(f"- `{file}`\n")
                f.write("\n")
                
            if modified:
                f.write("**Archivos Modificados:**\n")
                for file in modified:
                    f.write(f"- `{file}`\n")
                f.write("\n")
                
            if deleted:
                f.write("**Archivos Eliminados:**\n")
                for file in deleted:
                    f.write(f"- `{file}`\n")
                f.write("\n")
        
        f.write("---\n\n")
