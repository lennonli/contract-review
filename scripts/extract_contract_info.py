#!/usr/bin/env python3
"""
Enhanced Contract Information Extractor

Extracts key information from contract documents including parties, dates,
key terms, contract type identification, and creates a structured summary.

Usage:
    python extract_contract_info.py <contract_file_path> [--output json|text|md]
"""

import sys
import os
from pathlib import Path
import re
import json
from datetime import datetime


def extract_text(file_path):
    """Extract text from various file formats."""
    file_ext = Path(file_path).suffix.lower()

    if file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            # Also read tables
            for table in doc.tables:
                for row in table.rows:
                    text += '\n' + ' | '.join([cell.text for cell in row.cells])
            return text
        except ImportError:
            print("Error: python-docx not installed. Install with: pip install python-docx")
            sys.exit(1)
    elif file_ext == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except ImportError:
            print("Error: PyPDF2 not installed. Install with: pip install PyPDF2")
            sys.exit(1)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


# Contract type definitions with keywords
CONTRACT_TYPES = {
    'equity_shareholder': {
        'name_cn': '股权/股东协议',
        'name_en': 'Equity/Shareholder Agreement',
        'keywords': ['股东协议', '股权协议', '股权转让', 'Shareholder Agreement', 'Share Transfer', '股东会', '董事会席位'],
        'checklist': 'equity_shareholder.md'
    },
    'investment': {
        'name_cn': '投资协议',
        'name_en': 'Investment Agreement',
        'keywords': ['投资协议', '融资协议', 'Investment Agreement', '增资', '估值', 'Valuation', '优先股', 'Series A', 'Series B'],
        'checklist': 'investment.md'
    },
    'employment': {
        'name_cn': '劳动合同',
        'name_en': 'Employment Contract',
        'keywords': ['劳动合同', '雇佣协议', 'Employment', '试用期', '工资', '社会保险', '竞业限制', 'Probation'],
        'checklist': 'employment.md'
    },
    'lease': {
        'name_cn': '租赁协议',
        'name_en': 'Lease Agreement',
        'keywords': ['租赁协议', '租赁合同', '房屋租赁', 'Lease Agreement', '租金', '押金', '承租方', '出租方'],
        'checklist': 'lease.md'
    },
    'service': {
        'name_cn': '服务/咨询协议',
        'name_en': 'Service/Consulting Agreement',
        'keywords': ['服务协议', '咨询协议', 'Service Agreement', 'Consulting', '服务费', '交付物', 'Deliverables'],
        'checklist': 'service.md'
    },
    'sales_purchase': {
        'name_cn': '买卖/采购合同',
        'name_en': 'Sales/Purchase Contract',
        'keywords': ['买卖合同', '采购合同', '购销合同', 'Sales Contract', 'Purchase Agreement', '货物', '交付', '验收'],
        'checklist': 'sales_purchase.md'
    },
    'nda': {
        'name_cn': '保密协议',
        'name_en': 'Non-Disclosure Agreement',
        'keywords': ['保密协议', 'NDA', 'Non-Disclosure', 'Confidentiality Agreement', '保密信息', 'Confidential Information'],
        'checklist': 'nda.md'
    },
    'loan': {
        'name_cn': '借款协议',
        'name_en': 'Loan Agreement',
        'keywords': ['借款协议', '贷款合同', 'Loan Agreement', '借款人', '贷款人', '利率', '还款'],
        'checklist': 'loan.md'
    },
    'ip_license': {
        'name_cn': '知识产权许可协议',
        'name_en': 'IP License Agreement',
        'keywords': ['许可协议', '授权协议', 'License Agreement', '知识产权', '专利', '商标', '著作权', 'Royalty'],
        'checklist': 'ip_license.md'
    },
    'partnership': {
        'name_cn': '合作/合资协议',
        'name_en': 'Partnership/JV Agreement',
        'keywords': ['合作协议', '合资协议', 'Partnership', 'Joint Venture', '合资公司', '合作方'],
        'checklist': 'partnership_jv.md'
    }
}


def identify_contract_type(text):
    """Identify contract type based on keywords."""
    text_lower = text.lower()
    scores = {}

    for type_key, type_info in CONTRACT_TYPES.items():
        score = 0
        for keyword in type_info['keywords']:
            if keyword.lower() in text_lower:
                score += 1
        if score > 0:
            scores[type_key] = score

    if scores:
        best_match = max(scores, key=scores.get)
        return CONTRACT_TYPES[best_match]

    return {'name_cn': '未分类', 'name_en': 'Unclassified', 'checklist': None}


def extract_title(text):
    """Extract contract title."""
    lines = text.strip().split('\n')
    for line in lines[:10]:
        line = line.strip()
        if 10 < len(line) < 100:
            if any(kw in line for kw in ['协议', '合同', 'Agreement', 'Contract']):
                return line
    return "Unknown"


def extract_parties(text):
    """Extract contracting parties."""
    parties = []

    patterns = [
        r'甲方[（(]?[^）)]*[）)]?[：:]\s*([^\n（）()]+)',
        r'乙方[（(]?[^）)]*[）)]?[：:]\s*([^\n（）()]+)',
        r'丙方[（(]?[^）)]*[）)]?[：:]\s*([^\n（）()]+)',
        r'投资方[：:]\s*([^\n]+)',
        r'目标公司[：:]\s*([^\n]+)',
        r'出租方[：:]\s*([^\n]+)',
        r'承租方[：:]\s*([^\n]+)',
        r'服务方[：:]\s*([^\n]+)',
        r'委托方[：:]\s*([^\n]+)',
        r'Party A[:\s]+([^\n]+?)(?=\(|Party|$)',
        r'Party B[:\s]+([^\n]+?)(?=\(|Party|$)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().strip('：:').strip()
            if clean and len(clean) > 2 and clean not in parties:
                parties.append(clean)

    return parties[:10]


def extract_dates(text):
    """Extract important dates."""
    dates = {}

    # Chinese date patterns
    cn_date = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
    if cn_date:
        dates['签署日期'] = f"{cn_date.group(1)}年{cn_date.group(2)}月{cn_date.group(3)}日"

    # English date patterns
    en_date = re.search(r'Date[d]?[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})', text, re.IGNORECASE)
    if en_date:
        dates['execution_date'] = en_date.group(1)

    # Term/Duration
    term = re.search(r'(?:期限|Term)[：:]\s*([^\n]+)', text, re.IGNORECASE)
    if term:
        dates['期限/Term'] = term.group(1).strip()

    return dates


def extract_amounts(text):
    """Extract monetary amounts."""
    amounts = []

    # RMB patterns
    rmb = re.findall(r'(?:人民币|RMB|￥)\s*([\d,，]+(?:\.\d+)?)\s*(?:元|万元)?', text)
    for amt in rmb[:5]:
        amounts.append(f"RMB {amt}")

    # USD patterns
    usd = re.findall(r'(?:USD|\$)\s*([\d,]+(?:\.\d+)?)', text)
    for amt in usd[:5]:
        amounts.append(f"USD {amt}")

    return amounts


def extract_governing_law(text):
    """Extract governing law."""
    patterns = [
        r'(?:适用法律|准据法|Governing Law)[：:]\s*([^\n]+)',
        r'适用([^\n]*?法律)',
        r'governed by[^.]*laws? of ([^.\n]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def extract_dispute_resolution(text):
    """Extract dispute resolution clause."""
    if re.search(r'仲裁|arbitration|CIETAC|HKIAC|ICC', text, re.IGNORECASE):
        # Find arbitration institution
        inst = re.search(r'(CIETAC|中国国际经济贸易仲裁委员会|HKIAC|香港国际仲裁中心|ICC|新加坡国际仲裁中心|SIAC)', text)
        if inst:
            return f"仲裁 ({inst.group(1)})"
        return "仲裁"
    elif re.search(r'法院|诉讼|court|litigation|jurisdiction', text, re.IGNORECASE):
        return "诉讼/法院管辖"

    return None


def extract_contract_info(file_path):
    """Main extraction function."""
    text = extract_text(file_path)

    info = {
        'file_name': Path(file_path).name,
        'file_path': str(Path(file_path).absolute()),
        'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'contract_type': identify_contract_type(text),
        'contract_title': extract_title(text),
        'parties': extract_parties(text),
        'dates': extract_dates(text),
        'amounts': extract_amounts(text),
        'governing_law': extract_governing_law(text),
        'dispute_resolution': extract_dispute_resolution(text),
        'word_count': len(text),
        'language': 'Chinese' if re.search(r'[\u4e00-\u9fff]', text) else 'English'
    }

    return info


def format_as_text(info):
    """Format info as plain text."""
    lines = [
        "=" * 70,
        "合同信息提取报告 / Contract Information Extraction Report",
        "=" * 70,
        f"\n📄 文件: {info['file_name']}",
        f"📅 提取时间: {info['extraction_time']}",
        f"📝 字数: {info['word_count']}",
        f"🌐 语言: {info['language']}",
        f"\n📋 合同类型: {info['contract_type']['name_cn']} / {info['contract_type']['name_en']}",
        f"📑 合同标题: {info['contract_title']}",
    ]

    if info['parties']:
        lines.append("\n👥 合同各方:")
        for i, party in enumerate(info['parties'], 1):
            lines.append(f"   {i}. {party}")

    if info['dates']:
        lines.append("\n📅 重要日期:")
        for key, value in info['dates'].items():
            lines.append(f"   {key}: {value}")

    if info['amounts']:
        lines.append("\n💰 金额:")
        for amt in info['amounts']:
            lines.append(f"   {amt}")

    if info['governing_law']:
        lines.append(f"\n⚖️ 适用法律: {info['governing_law']}")

    if info['dispute_resolution']:
        lines.append(f"🏛️ 争议解决: {info['dispute_resolution']}")

    if info['contract_type'].get('checklist'):
        lines.append(f"\n📋 建议使用检查清单: {info['contract_type']['checklist']}")

    lines.append("\n" + "=" * 70)

    return '\n'.join(lines)


def format_as_markdown(info):
    """Format info as markdown."""
    lines = [
        "# 合同信息提取报告",
        "",
        "## 基本信息",
        "",
        "| 项目 | 内容 |",
        "|------|------|",
        f"| 文件名 | {info['file_name']} |",
        f"| 提取时间 | {info['extraction_time']} |",
        f"| 合同类型 | {info['contract_type']['name_cn']} |",
        f"| 语言 | {info['language']} |",
        f"| 字数 | {info['word_count']} |",
        "",
        f"## 合同标题",
        "",
        f"{info['contract_title']}",
        "",
    ]

    if info['parties']:
        lines.extend(["## 合同各方", ""])
        for i, party in enumerate(info['parties'], 1):
            lines.append(f"{i}. {party}")
        lines.append("")

    if info['dates']:
        lines.extend(["## 重要日期", ""])
        for key, value in info['dates'].items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")

    if info['amounts']:
        lines.extend(["## 涉及金额", ""])
        for amt in info['amounts']:
            lines.append(f"- {amt}")
        lines.append("")

    if info['governing_law'] or info['dispute_resolution']:
        lines.extend(["## 法律条款", ""])
        if info['governing_law']:
            lines.append(f"- **适用法律**: {info['governing_law']}")
        if info['dispute_resolution']:
            lines.append(f"- **争议解决**: {info['dispute_resolution']}")
        lines.append("")

    return '\n'.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract key information from contracts")
    parser.add_argument("file_path", help="Path to contract file")
    parser.add_argument("--output", "-o", choices=['json', 'text', 'md'], default='text',
                        help="Output format (default: text)")
    parser.add_argument("--save", "-s", help="Save output to file")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)

    info = extract_contract_info(args.file_path)

    if args.output == 'json':
        output = json.dumps(info, ensure_ascii=False, indent=2)
    elif args.output == 'md':
        output = format_as_markdown(info)
    else:
        output = format_as_text(info)

    print(output)

    if args.save:
        with open(args.save, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n✅ Saved to: {args.save}")


if __name__ == '__main__':
    main()
