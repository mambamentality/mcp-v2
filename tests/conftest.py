import sys
from pathlib import Path

# Permite `import tools....` al correr pytest desde cualquier directorio,
# agregando la raíz del proyecto (donde vive function_app.py) al sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
