# Task 2.1 Wiki generation prompt

Task 2.1 defines a provider-neutral prompt and a structural output contract. It
does not call an LLM or select a model. Task 2.2 can later connect this contract
to the chosen LLM integration.

## Fixed Wiki structure

Generated pages must contain one project-title heading followed by these seven
level-two headings exactly once and in this order:

```markdown
# <Project Title>

## ภาพรวมโครงงาน
## ปัญหาและที่มา
## วัตถุประสงค์
## เครื่องมือและเทคโนโลยี
## วิธีดำเนินงาน
## ผลลัพธ์
## สรุป
```

Fixed headings make generated pages predictable for reviewers and allow later
code to validate, display, and eventually chunk equivalent sections without
depending on a particular LLM's preferred wording.

## Prompt rules

The prompt separates immutable instructions from extracted source text with
explicit `SOURCE_DOCUMENT` delimiters. It requires Markdown-only output,
source-supported statements, concise summarization, and preservation of Thai
names and established English technical terms. It forbids invented facts,
references, results, technologies, authors, and metrics.

When the report does not support an important required section, the generated
page must use `ไม่พบข้อมูลในเอกสารต้นฉบับ` instead of guessing. Text inside the
source delimiters is treated as untrusted document data rather than additional
instructions.

## Validation and Task 2.2 handoff

`validate_wiki_markdown` checks the title and fixed level-two structure only. It
does not judge writing quality or factual accuracy. Task 2.2 will provide the
prompt returned by `build_wiki_generation_prompt` to an LLM and can reject or
retry structurally invalid output using this validator.
