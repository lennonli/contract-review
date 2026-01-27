#!/usr/bin/env python3
"""
Read Full DOCX Content

Reads and displays the complete text content from a DOCX file,
including paragraphs and tables.

Usage:
    python read_full_docx.py <file_path>
"""

import sys
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("Error: python-docx not installed. Install with: pip install python-docx")
    sys.exit(1)


def read_docx(file_path):
    """Read all content from a DOCX file."""
    try:
        doc = Document(file_path)
        content = []

        # Read paragraphs
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                content.append(para.text)

        # Read tables
        for table_idx, table in enumerate(doc.tables):
            content.append(f"\n[Table {table_idx + 1}]")
            for row in table.rows:
                row_text = ' | '.join([cell.text.strip() for cell in row.cells])
                if row_text.strip():
                    content.append(row_text)

        return '\n'.join(content)

    except Exception as e:
        return f"Error reading file: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python read_full_docx.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    content = read_docx(file_path)
    print(content)


if __name__ == "__main__":
    main()
