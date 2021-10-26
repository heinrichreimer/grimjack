from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "index"
TOPICS_DIR = DATA_DIR / "topics"

_BASE_DIRS = [DATA_DIR, DOCUMENTS_DIR, TOPICS_DIR, INDEX_DIR]
for path in _BASE_DIRS:
    path.mkdir(parents=True, exist_ok=True)

DEFAULT_DOCUMENTS_ZIP_URL = (
    "https://files.webis.de/corpora/corpora-webis/corpus-touche-task2-22/"
    "touche-task2-passages-version-001.zip"
)
DEFAULT_TOPICS_ZIP_URL = (
    "https://webis.de/events/touche-22/data/topics-task2-2022.zip"
)