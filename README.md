# 📦 Салбар дээр үлдэгдэлгүй бараа — Dashboard

Live dashboard that shows which items are missing from each branch (compared to warehouse stock), and highlights imbalanced stock distribution.

---

## 🚀 One-time setup

### 1. Create a GitHub repository

Go to https://github.com/new and create a **public** repository (required for free GitHub Pages).

### 2. Upload this project

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/bayarchiglel/salbar.git
git push -u origin main
```

### 3. Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages**
2. Under *Source*, choose **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click **Save**

Your dashboard will be live at:
`https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

## 🔄 Daily update workflow

Every time you get a new Excel export from your ERP:

1. **Replace** `data/нийт.xlsx` with the new file (keep the same filename)
2. **Commit & push**:

```bash
# drag the new file into the data/ folder, then:
git add data/нийт.xlsx
git commit -m "update stock data $(date +%Y-%m-%d)"
git push
```

GitHub Actions will automatically:
- Run `scripts/build_data.py`
- Rebuild `data/stock.json`
- Commit the result back
- The live dashboard refreshes on next page load ✅

You can also trigger a rebuild manually:  
Repo → **Actions** → **Build dashboard data** → **Run workflow**

---

## 📁 Project structure

```
├── index.html              ← Dashboard (loads data/stock.json)
├── data/
│   ├── нийт.xlsx           ← ← ← Replace this file to update
│   └── stock.json          ← Auto-generated, do not edit manually
├── scripts/
│   └── build_data.py       ← Converts Excel → stock.json
└── .github/
    └── workflows/
        └── build.yml       ← GitHub Actions workflow
```

---

## 🛠 Run locally

```bash
pip install pandas openpyxl
python scripts/build_data.py

# Then open index.html with a local server (required — file:// won't work for fetch())
python -m http.server 8000
# → http://localhost:8000
```

> **Why a local server?** The dashboard fetches `data/stock.json` via HTTP.  
> Opening `index.html` directly as a file (`file://`) blocks that fetch in most browsers.
