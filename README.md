# Data Viz Tool

A flexible, dynamic, AI-powered data visualization platform for building interactive dashboards, exploring custom data sources, and generating rich PDF reports.

---

## 🚀 Overview
The **Data Viz Tool** allows users to:
- Build **interactive dashboards** with charts, tables, text blocks, KPIs, and custom components.
- Arrange components in **tabs**, **rows**, and **columns** to create clean layouts.
- Connect to **custom data sources**, including CSV, databases, APIs, and more.
- Use **AI-powered enrichment** to generate summaries, insights, commentary, and chart explanations.
- Export full reports as **PDF** using a headless browser (Playwright).

---

## ✨ Features

### 🔧 Modular Dashboard Builder
- Drag-and-drop style component selection (charts, text blocks, tables, KPIs).
- Support for multiple **layouts**:
  - Tabs
  - Multi-column rows
  - Vertical stacks

### 📊 Interactive Charts
Supports multiple dynamic chart types, such as:
- Line, bar, scatter, area
- Pie, donut, funnel
- Multi-axis charts
- Time-series charts

Charts automatically update based on user input or refreshed data.

### 🔗 Custom Data Sources
Load data from:
- Local files (CSV, Excel, Parquet)
- SQL databases
- REST APIs
- User-entered pandas DataFrames

### 🤖 AI Integration
Use LLMs (OpenAI, Anthropic, Groq, Gemini, etc.) to:
- Describe datasets
- Suggest relevant charts
- Summarize dashboards
- Generate insights and recommendations
- Enrich PDF reports with text and commentary

### 📄 PDF Report Generation
- One-click **"Download PDF"** button
- Uses Playwright (chromium headless) for high-quality rendering
- Supports CSS styling for brand-aligned exports

---

## 🗂️ Project Structure
# Useful Commands

Activate virtual environment
```
.\.venv\Scripts\activate
```
 
Install pipenv
 ```
pip install pipenv
 ```


Create New venv
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version

```

# Deploy

⭐ How to Use
Patch version (default):

1.2.3 → 1.2.4
```
powershell -File deploy.ps1 -patch "Fix: dashboard alignment issue"
```
Minor version:

1.2.3 → 1.3.0
```
powershell -File deploy.ps1 -minor "Feat: added charts section"
```
Major version:

1.2.3 → 2.0.0
```
powershell -File deploy.ps1 -major "BREAKING: reworked API"
```

⚡ Requirements

pytest installed (pipenv install pytest)

flake8 installed (pipenv install flake8)

black installed (pipenv install black)

mypy installed (pipenv install mypy)


playwright install
