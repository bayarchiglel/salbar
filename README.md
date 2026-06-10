# 📦 Салбар үлдэгдэл Dashboard

ERP stock dashboard — shows items missing from branches vs warehouse, plus imbalanced stock distribution across branches.

## Features
- 🔍 **Missing items** per branch (Жижиг / Том бараа)
- ⚖️ **Imbalanced stock** view comparing all branches
- 📂 **Category / Subcategory** multi-select filters
- 🏭 **Warehouse view**: combined total OR expanded per-warehouse breakdown
- 📥 **Export to Excel** with date & branch title header
- 🖨️ **Export to PDF** via browser print
- 🔎 **Multi-select dropdowns** for all filters (like Excel filter)

## Excel columns expected
| Column | Required | Notes |
|--------|----------|-------|
| Салбар | ✅ | Branch / warehouse name |
| Барааны код | ✅ | Item code |
| Барааны нэр | ✅ | Item name |
| Тоо | ✅ | Quantity |
| Байршил | ✅ | `Жижиг бараа` or `Том бараа` |
| Ангилал | ⬜ Optional | Category |
| Дэд ангилал | ⬜ Optional | Subcategory |

Category/Subcategory columns are optional — if not present the filter just won't appear.

## One-time GitHub setup

```bash
git init
git add .
git commit -m "initial"
git branch -M main
git remote add origin https://github.com/YOUR/REPO.git
git push -u origin main
```

Then: **Settings → Pages → Source: main / (root) → Save**

Live at: `https://YOUR.github.io/REPO/`

## Daily update

Replace `data/нийт.xlsx` then:

```bash
git add data/нийт.xlsx
git commit -m "stock update $(date +%Y-%m-%d)"
git push
```

GitHub Actions rebuilds `data/stock.json` automatically (~1 min).

## Run locally

```bash
pip install pandas openpyxl
python scripts/build_data.py
python -m http.server 8000
# open http://localhost:8000
```

## Project structure

```
├── index.html                  ← Dashboard
├── data/
│   ├── нийт.xlsx               ← ← Replace to update
│   └── stock.json              ← Auto-generated
├── scripts/
│   └── build_data.py           ← Excel → JSON converter
└── .github/workflows/build.yml ← Auto-rebuild on push
```
