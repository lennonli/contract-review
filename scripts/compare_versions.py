#!/usr/bin/env python3
"""
Contract Version Comparison Tool

Compare two versions of a contract and generate a detailed diff report.

Usage:
    python compare_versions.py version1.docx version2.docx [--output report.md]
"""

import sys
import os
import argparse
import difflib
from datetime import datetime
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("Error: python-docx not installed. Install with: pip install python-docx")
    sys.exit(1)


def extract_text_from_docx(file_path):
    """Extract all text from a DOCX file."""
    doc = Document(file_path)
    paragraphs = []

    # Extract from paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = ' | '.join([cell.text.strip() for cell in row.cells])
            if row_text.strip():
                paragraphs.append(row_text)

    return paragraphs


def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return [line.strip() for line in text.split('\n') if line.strip()]
    except ImportError:
        print("Error: PyPDF2 not installed. Install with: pip install PyPDF2")
        sys.exit(1)


def extract_text(file_path):
    """Extract text based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def categorize_change(old_text, new_text):
    """Categorize the type and risk level of a change."""
    old_lower = old_text.lower() if old_text else ""
    new_lower = new_text.lower() if new_text else ""

    # High risk keywords
    high_risk_keywords = [
        '违约', '赔偿', '责任', '解除', '终止', '保证', '担保',
        '不可抗力', '仲裁', '诉讼', '管辖', '知识产权', '保密',
        'liability', 'indemnify', 'terminate', 'breach', 'warranty',
        'guarantee', 'arbitration', 'jurisdiction', 'confidential'
    ]

    # Medium risk keywords
    medium_risk_keywords = [
        '期限', '金额', '比例', '费用', '付款', '交付',
        '验收', '质量', '标准', '变更',
        'term', 'amount', 'payment', 'delivery', 'acceptance', 'quality'
    ]

    combined = old_lower + new_lower

    for keyword in high_risk_keywords:
        if keyword in combined:
            return '🔴 高风险', 'Critical'

    for keyword in medium_risk_keywords:
        if keyword in combined:
            return '🟡 中等风险', 'Medium'

    return '🟢 低风险', 'Low'


def compare_contracts(file1, file2):
    """Compare two contract files and return differences."""
    text1 = extract_text(file1)
    text2 = extract_text(file2)

    differ = difflib.SequenceMatcher(None, text1, text2)

    changes = {
        'added': [],
        'deleted': [],
        'modified': []
    }

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'replace':
            for old, new in zip(text1[i1:i2], text2[j1:j2]):
                risk_label, risk_level = categorize_change(old, new)
                changes['modified'].append({
                    'old': old,
                    'new': new,
                    'risk_label': risk_label,
                    'risk_level': risk_level
                })
        elif tag == 'delete':
            for line in text1[i1:i2]:
                risk_label, risk_level = categorize_change(line, '')
                changes['deleted'].append({
                    'text': line,
                    'risk_label': risk_label,
                    'risk_level': risk_level
                })
        elif tag == 'insert':
            for line in text2[j1:j2]:
                risk_label, risk_level = categorize_change('', line)
                changes['added'].append({
                    'text': line,
                    'risk_label': risk_label,
                    'risk_level': risk_level
                })

    return changes


def generate_report(file1, file2, changes, output_path=None):
    """Generate a markdown comparison report."""
    report = []

    # Header
    report.append("# 合同版本对比报告 / Contract Version Comparison Report")
    report.append("")
    report.append("## 基本信息 / Basic Information")
    report.append("")
    report.append(f"| 项目 | 内容 |")
    report.append(f"|------|------|")
    report.append(f"| 版本1 / Version 1 | {Path(file1).name} |")
    report.append(f"| 版本2 / Version 2 | {Path(file2).name} |")
    report.append(f"| 对比时间 / Comparison Time | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    report.append("")

    # Summary
    total_changes = len(changes['added']) + len(changes['deleted']) + len(changes['modified'])
    critical_count = sum(1 for c in changes['modified'] if c['risk_level'] == 'Critical')
    critical_count += sum(1 for c in changes['added'] if c['risk_level'] == 'Critical')
    critical_count += sum(1 for c in changes['deleted'] if c['risk_level'] == 'Critical')

    report.append("## 变更摘要 / Change Summary")
    report.append("")
    report.append(f"| 变更类型 | 数量 |")
    report.append(f"|----------|------|")
    report.append(f"| 新增 / Added | {len(changes['added'])} |")
    report.append(f"| 删除 / Deleted | {len(changes['deleted'])} |")
    report.append(f"| 修改 / Modified | {len(changes['modified'])} |")
    report.append(f"| **总计 / Total** | **{total_changes}** |")
    report.append(f"| ⚠️ 高风险变更 / Critical | {critical_count} |")
    report.append("")

    # Modified content
    if changes['modified']:
        report.append("## 修改内容 / Modified Content")
        report.append("")
        for i, change in enumerate(changes['modified'], 1):
            report.append(f"### 修改 {i} {change['risk_label']}")
            report.append("")
            report.append("**原文 / Original:**")
            report.append(f"> {change['old']}")
            report.append("")
            report.append("**修改后 / Modified:**")
            report.append(f"> {change['new']}")
            report.append("")
            report.append("---")
            report.append("")

    # Added content
    if changes['added']:
        report.append("## 新增内容 / Added Content")
        report.append("")
        for i, change in enumerate(changes['added'], 1):
            report.append(f"### 新增 {i} {change['risk_label']}")
            report.append("")
            report.append(f"> {change['text']}")
            report.append("")

    # Deleted content
    if changes['deleted']:
        report.append("## 删除内容 / Deleted Content")
        report.append("")
        for i, change in enumerate(changes['deleted'], 1):
            report.append(f"### 删除 {i} {change['risk_label']}")
            report.append("")
            report.append(f"> ~~{change['text']}~~")
            report.append("")

    # Footer
    report.append("---")
    report.append("")
    report.append("*本报告由 Contract Review AI 自动生成*")

    report_text = '\n'.join(report)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"✅ Report saved to: {output_path}")

    return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Compare two contract versions and generate a diff report."
    )
    parser.add_argument("file1", help="First version (older)")
    parser.add_argument("file2", help="Second version (newer)")
    parser.add_argument("--output", "-o", help="Output report path (default: comparison_report.md)")

    args = parser.parse_args()

    # Validate files
    for f in [args.file1, args.file2]:
        if not os.path.exists(f):
            print(f"Error: File not found: {f}")
            sys.exit(1)

    # Default output path
    if not args.output:
        args.output = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    # Compare and generate report
    print(f"Comparing: {args.file1} vs {args.file2}")
    changes = compare_contracts(args.file1, args.file2)
    report = generate_report(args.file1, args.file2, changes, args.output)

    # Print summary
    total = len(changes['added']) + len(changes['deleted']) + len(changes['modified'])
    print(f"\n📊 Found {total} differences:")
    print(f"   + {len(changes['added'])} added")
    print(f"   - {len(changes['deleted'])} deleted")
    print(f"   ~ {len(changes['modified'])} modified")


if __name__ == "__main__":
    main()
