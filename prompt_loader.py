import csv
from pathlib import Path

def load_prompts_from_file(file_path: str) -> list[str]:
    """
    Load prompts from a text or CSV file
    
    Args:
        file_path: Path to prompt file (.txt or .csv)
    
    Returns:
        List of prompt strings
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    ext = path.suffix.lower()
    
    if ext in {".csv", ".tsv"}:
        return _load_from_csv(path)
    elif ext == ".txt":
        return _load_from_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def _load_from_csv(path: Path) -> list[str]:
    """Load prompts from CSV file (first column)"""
    print(f"📄 Reading CSV: {path.name}")
    prompts = []
    
    with path.open(encoding="utf-8-sig", newline="") as f:
        try:
            # Try to detect dialect
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        except csv.Error:
            f.seek(0)
            dialect = csv.get_dialect("excel")
        
        reader = csv.reader(f, dialect)
        
        # Check if first row is header
        first_row = next(reader, [])
        if first_row and first_row[0].lower().strip() != "prompt":
            # Not a header, add it as prompt
            if first_row[0].strip():
                prompts.append(first_row[0].strip())
        
        # Read remaining rows
        for row in reader:
            if row and row[0].strip():
                prompts.append(row[0].strip())
    
    print(f"   ✅ Loaded {len(prompts)} prompt(s)")
    return prompts

def _load_from_txt(path: Path) -> list[str]:
    """Load prompts from text file (one per line)"""
    print(f"📄 Reading TXT: {path.name}")
    
    content = path.read_text(encoding="utf-8")
    prompts = [line.strip() for line in content.splitlines() if line.strip()]
    
    print(f"   ✅ Loaded {len(prompts)} prompt(s)")
    return prompts
