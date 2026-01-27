# Changelog / 更新日志

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-01-27

### 🎉 重大更新 / Major Release

本版本是一次重大升级，将工作流程从 7 步扩展到 9 步，新增多项专业功能，显著提升合同审核的专业性和效率。

This is a major release that expands the workflow from 7 steps to 9 steps, adding multiple professional features that significantly improve the professionalism and efficiency of contract review.

---

### ✨ 新增功能 / Added

#### 新增工作流程步骤 / New Workflow Steps

- **Step 0: 合同类型自动识别 (Contract Type Identification)**
  - 支持 10 种合同类型的自动识别
  - 自动加载对应的专项检查清单
  - 支持类型：股权协议、投资协议、劳动合同、租赁协议、服务协议、买卖合同、保密协议、借款协议、知识产权许可、合资协议

- **Step 0.5: 审核范围确认 (Scope Confirmation)**
  - 询问客户代表哪一方（甲方/乙方/投资方等）
  - 确认重点关注领域（知识产权、违约责任等）
  - 确认行业特殊合规要求（金融、医疗、数据隐私等）

- **Step 8: 版本对比功能 (Version Comparison)**
  - 对比两个合同版本的差异
  - 自动标注变更的风险等级
  - 生成详细的对比报告

#### 新增参考文档 / New Reference Documents

- **`references/legal_references.md`** - 法律法规速查手册
  - 覆盖 9 大法律领域：合同法、劳动法、公司法、知识产权法、数据隐私法等
  - 包含《民法典》《劳动合同法》《公司法》《个人信息保护法》等核心法条
  - 风险对应法条速查表

- **`references/contract_types/`** - 分类型专项检查清单
  - `equity_shareholder.md` - 股权/股东协议专项清单（含股权结构、转让限制、公司治理、退出机制等）
  - `investment.md` - 投资协议专项清单（含交易结构、先决条件、投资人权利、对赌条款等）
  - `employment.md` - 劳动合同专项清单（含试用期、薪酬、社保、竞业限制等，含法定限制提醒）
  - `lease.md` - 租赁协议专项清单
  - `service.md` - 服务/咨询协议专项清单
  - `sales_purchase.md` - 买卖/采购合同专项清单
  - `nda.md` - 保密协议专项清单

#### 新增工具脚本 / New Scripts

- **`scripts/compare_versions.py`** - 合同版本对比工具
  - 支持 .docx、.pdf、.txt 格式
  - 自动分类变更类型（新增/删除/修改）
  - 自动评估变更风险等级
  - 生成 Markdown 格式对比报告

#### 新增模板 / New Templates

- **`templates/legal_opinion_template.md`** - 法律意见书标准模板
  - 专业的文档结构
  - 包含 Mermaid 业务流程图
  - 修改清单汇总表
  - 结论与建议模块

---

### 🔧 增强功能 / Enhanced

#### 风险分析增强 (Step 1)

- **法律依据引用**: 每个风险点现在都引用具体法条
  ```
  ▸ 法律依据 / Legal Basis: 《民法典》第XXX条
  ```
- **原文摘录**: 增加对原合同条款的直接引用
- **格式美化**: 使用更清晰的结构化输出格式

#### 缺失条款分析增强 (Step 2)

- 交叉引用专项检查清单
- 提供完整的建议条款文字
- 标注建议插入位置

#### 全面校对增强 (Step 3)

- 新增检查类别：交叉引用、定义一致性
- 更详细的问题描述和修正建议

#### 法律意见书增强 (Step 4)

- **Mermaid 业务流程图**: 自动生成合同业务流程可视化
- **修改清单汇总表**: 按风险等级排序的完整修改清单
- **专项合规检查**: 根据合同类型的特殊合规审查
- **结论与建议**: 更结构化的行动建议（必须修改/建议修改/可选优化）

#### 自动修订增强 (Step 6)

- 增强的错误处理和日志记录
- 支持 JSON 格式的修订清单输入
- 更好的 Track Changes 格式保留
- 失败时提供手动修改指南

#### 脚本增强

- **`revise_contract.py`**:
  - 新增 `--revisions-file` 参数支持 JSON 输入
  - 新增 `--author` 参数自定义修订作者
  - 新增 `--verbose` 参数详细日志
  - 增强的空白字符和格式保留
  - 支持表格内容修订

- **`extract_contract_info.py`**:
  - 新增合同类型自动识别
  - 新增争议解决方式提取
  - 支持多种输出格式（text/json/md）
  - 新增 `--save` 参数保存到文件

---

### 🌐 多语言支持 / Internationalization

- **输出语言自动匹配**: 根据合同原文语言自动选择输出语言
- **中英双语文档**: 所有参考文档和模板均为中英双语
- **双语触发词**: 支持中文和英文触发词

---

### 📋 工作流程变更对比 / Workflow Comparison

| 步骤 | v1.0 | v2.0 | 变更说明 |
|------|------|------|----------|
| Step 0 | ❌ | ✅ 合同类型识别 | 🆕 新增 |
| Step 0.5 | ❌ | ✅ 审核范围确认 | 🆕 新增 |
| Step 1 | ✅ 风险分析 | ✅ 风险分析 + 法律依据 | 🔧 增强 |
| Step 2 | ✅ 缺失条款 | ✅ 缺失条款 | 🔧 增强 |
| Step 3 | ✅ 全面校对 | ✅ 全面校对 | 🔧 增强 |
| Step 4 | ✅ 法律意见书 | ✅ 法律意见书 + 流程图 | 🔧 增强 |
| Step 5 | ✅ 用户确认 | ✅ 用户确认 | ➖ 无变化 |
| Step 6 | ✅ 自动修订 | ✅ 自动修订 | 🔧 增强 |
| Step 7 | ✅ 修改总结 | ✅ 修改总结 | ➖ 无变化 |
| Step 8 | ❌ | ✅ 版本对比 | 🆕 新增 |

---

### 🐛 修复 / Fixed

- 修复了 Track Changes 中空白字符丢失的问题
- 修复了表格内容无法修订的问题
- 改进了中文字符的编码处理

---

### 📦 依赖 / Dependencies

- `python-docx` >= 0.8.11 (用于 DOCX 处理)
- `PyPDF2` >= 3.0.0 (用于 PDF 处理，可选)

---

### ⚠️ 破坏性变更 / Breaking Changes

- 脚本路径从 `~/.gemini/antigravity/skills/` 变更为 `~/.claude/skills/`
- 修订脚本的命令行参数格式略有调整（向后兼容）

---

### 🙏 致谢 / Acknowledgements

感谢所有提供反馈和建议的用户。

---

## [1.0.0] - 2026-01-19

### 初始版本 / Initial Release

- 7 步标准化合同审核工作流程
- 风险分析（核心/中等/低级三级分类）
- 缺失条款分析
- 全面校对
- 法律意见书生成
- 用户确认流程
- 自动修订（Track Changes）
- 修改重点总结
- 基础参考文档（common_clauses.md, review_checklist.md）
- 合同修订脚本（revise_contract.py）
- 合同读取脚本（read_full_docx.py）
- 合同信息提取脚本（extract_contract_info.py）
