#!/usr/bin/env python3
"""
Enhanced Contract Revision Script with Track Changes

This script applies revisions to a DOCX file using native Word Track Changes.
Enhanced version with better error handling, formatting preservation, and logging.

Usage:
    python revise_contract.py <input_file> --revisions "old|new;;old2|new2" [--output output.docx] [--open]
"""

import sys
import os
import argparse
import time
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
except ImportError:
    print("Error: python-docx not installed. Install with: pip install python-docx")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_AUTHOR = "Contract-Review-AI"
REVISION_ID_COUNTER = int(time.time() * 1000)


def get_next_revision_id():
    """Generate unique revision ID."""
    global REVISION_ID_COUNTER
    REVISION_ID_COUNTER += 1
    return str(REVISION_ID_COUNTER)


def create_ins_element(text, author=DEFAULT_AUTHOR, date_str=None):
    """Create a Word Track Changes insertion element (w:ins)."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    run = OxmlElement('w:r')

    # Preserve formatting - add run properties
    rPr = OxmlElement('w:rPr')
    run.append(rPr)

    text_el = OxmlElement('w:t')
    text_el.set(qn('xml:space'), 'preserve')  # Preserve whitespace
    text_el.text = text
    run.append(text_el)

    ins = OxmlElement('w:ins')
    ins.set(qn('w:id'), get_next_revision_id())
    ins.set(qn('w:author'), author)
    ins.set(qn('w:date'), date_str)
    ins.append(run)

    return ins


def create_del_element(text, author=DEFAULT_AUTHOR, date_str=None):
    """Create a Word Track Changes deletion element (w:del)."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    run = OxmlElement('w:r')
    del_text = OxmlElement('w:delText')
    del_text.set(qn('xml:space'), 'preserve')  # Preserve whitespace
    del_text.text = text
    run.append(del_text)

    del_el = OxmlElement('w:del')
    del_el.set(qn('w:id'), get_next_revision_id())
    del_el.set(qn('w:author'), author)
    del_el.set(qn('w:date'), date_str)
    del_el.append(run)

    return del_el


def enable_track_changes(doc):
    """Enable track changes in the document settings."""
    settings = doc.settings.element
    track_revisions = settings.find(qn('w:trackRevisions'))
    if track_revisions is None:
        track_revisions = OxmlElement('w:trackRevisions')
        settings.append(track_revisions)


def find_and_replace_in_paragraph(paragraph, original_text, revised_text, author=DEFAULT_AUTHOR):
    """
    Find and replace text in a paragraph with track changes.
    Returns True if replacement was made, False otherwise.
    """
    if original_text not in paragraph.text:
        return False

    # Get the full paragraph text
    full_text = paragraph.text

    # Find the position of the original text
    start_pos = full_text.find(original_text)
    if start_pos == -1:
        return False

    # Split into before, match, and after
    before_text = full_text[:start_pos]
    after_text = full_text[start_pos + len(original_text):]

    # Clear existing runs
    paragraph.clear()

    # Rebuild paragraph with track changes
    # 1. Add text before the change
    if before_text:
        run = paragraph.add_run(before_text)

    # 2. Add deletion marker for original text
    paragraph._element.append(create_del_element(original_text, author))

    # 3. Add insertion marker for new text (if not empty)
    if revised_text:
        paragraph._element.append(create_ins_element(revised_text, author))

    # 4. Add text after the change
    if after_text:
        run = paragraph.add_run(after_text)

    return True


def find_and_replace_in_tables(doc, original_text, revised_text, author=DEFAULT_AUTHOR):
    """Find and replace text in all tables."""
    replacements = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if find_and_replace_in_paragraph(paragraph, original_text, revised_text, author):
                        replacements += 1
    return replacements


def apply_revisions(doc_path, output_path, revisions, author=DEFAULT_AUTHOR):
    """
    Apply revisions to a DOCX file using native Track Changes.

    Args:
        doc_path: Path to original .docx file
        output_path: Path to save revised file
        revisions: List of dicts {'original': 'text to find', 'revised': 'new text'}
        author: Author name for track changes

    Returns:
        dict with statistics about the revisions applied
    """
    stats = {
        'total_revisions': len(revisions),
        'successful': 0,
        'failed': 0,
        'failed_items': []
    }

    # Validate input file
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Input file not found: {doc_path}")

    # Load document
    try:
        doc = Document(doc_path)
        logger.info(f"Loaded document: {doc_path}")
    except Exception as e:
        raise Exception(f"Error loading document: {e}")

    # Enable track changes
    enable_track_changes(doc)

    # Apply each revision
    for i, rev in enumerate(revisions):
        original_text = rev.get('original', '').strip()
        revised_text = rev.get('revised', '')

        if not original_text:
            logger.warning(f"Revision {i+1}: Empty original text, skipping")
            continue

        found = False

        # Search in paragraphs
        for paragraph in doc.paragraphs:
            if find_and_replace_in_paragraph(paragraph, original_text, revised_text, author):
                found = True
                stats['successful'] += 1
                logger.info(f"Revision {i+1}: Applied successfully")
                break  # Only replace first occurrence per revision

        # If not found in paragraphs, search in tables
        if not found:
            table_replacements = find_and_replace_in_tables(doc, original_text, revised_text, author)
            if table_replacements > 0:
                found = True
                stats['successful'] += 1
                logger.info(f"Revision {i+1}: Applied in table")

        if not found:
            stats['failed'] += 1
            preview = original_text[:50] + "..." if len(original_text) > 50 else original_text
            stats['failed_items'].append(preview)
            logger.warning(f"Revision {i+1}: Text not found: '{preview}'")

    # Save document
    try:
        doc.save(output_path)
        logger.info(f"Saved revised document to: {output_path}")
    except Exception as e:
        raise Exception(f"Error saving document: {e}")

    return stats


def parse_revisions_string(revisions_str):
    """
    Parse revisions from command line format.
    Format: "original text"|"new text";;"original text 2"|"new text 2"
    """
    revisions = []
    raw_revs = revisions_str.split(';;')

    for r in raw_revs:
        r = r.strip()
        if not r:
            continue
        if '|' in r:
            parts = r.split('|', 1)  # Split only on first |
            orig = parts[0].strip().strip('"').strip("'")
            new = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ''
            if orig:  # Only add if original text is not empty
                revisions.append({'original': orig, 'revised': new})

    return revisions


def parse_revisions_json(json_path):
    """
    Parse revisions from a JSON file.
    Expected format: [{"original": "text", "revised": "text"}, ...]
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Apply Track Changes revisions to a contract document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple revision
  python revise_contract.py contract.docx --revisions "old text|new text"

  # Multiple revisions
  python revise_contract.py contract.docx --revisions "old1|new1;;old2|new2"

  # Using JSON file for revisions
  python revise_contract.py contract.docx --revisions-file revisions.json

  # Custom output and open after saving
  python revise_contract.py contract.docx --revisions "old|new" --output revised.docx --open
        """
    )

    parser.add_argument("input_file", help="Path to original .docx file")
    parser.add_argument("--revisions", help="Revisions in format: 'old|new;;old2|new2'")
    parser.add_argument("--revisions-file", help="JSON file containing revisions")
    parser.add_argument("--output", help="Output file path (default: input_revised.docx)")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="Author name for track changes")
    parser.add_argument("--open", action="store_true", help="Open the file after saving (macOS/Windows)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse revisions
    revisions_list = []
    if args.revisions:
        revisions_list = parse_revisions_string(args.revisions)
    elif args.revisions_file:
        revisions_list = parse_revisions_json(args.revisions_file)
    else:
        print("Error: Either --revisions or --revisions-file is required")
        sys.exit(1)

    if not revisions_list:
        print("Error: No valid revisions found")
        sys.exit(1)

    logger.info(f"Parsed {len(revisions_list)} revision(s)")

    # Determine output path
    if not args.output:
        base, ext = os.path.splitext(args.input_file)
        date_str = datetime.now().strftime("%Y%m%d")
        args.output = f"{base}-ABL-{date_str}{ext}"

    # Apply revisions
    try:
        stats = apply_revisions(
            args.input_file,
            args.output,
            revisions_list,
            args.author
        )

        # Print summary
        print("\n" + "=" * 60)
        print("📋 Contract Revision Summary")
        print("=" * 60)
        print(f"Input file:  {args.input_file}")
        print(f"Output file: {args.output}")
        print(f"Author:      {args.author}")
        print("-" * 60)
        print(f"Total revisions:      {stats['total_revisions']}")
        print(f"Successfully applied: {stats['successful']}")
        print(f"Failed to apply:      {stats['failed']}")

        if stats['failed_items']:
            print("\n⚠️  Failed revisions (text not found):")
            for item in stats['failed_items']:
                print(f"   - \"{item}\"")

        print("=" * 60)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Open file if requested
    if args.open:
        try:
            import subprocess
            import platform

            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', args.output], check=True)
            elif system == 'Windows':
                os.startfile(args.output)
            elif system == 'Linux':
                subprocess.run(['xdg-open', args.output], check=True)

            print(f"\n📂 Opened: {args.output}")
        except Exception as e:
            print(f"⚠️  Could not open file: {e}")


if __name__ == "__main__":
    main()
