#!/usr/bin/env python3
"""
Convert нийт.xlsx → data/stock.json
Supports columns: Салбар, Барааны код, Барааны нэр, Тоо, Байршил, Ангилал, Дэд ангилал
Run: python scripts/build_data.py
"""

import pandas as pd
import json
import sys
from pathlib import Path

ROOT  = Path(__file__).parent.parent
EXCEL = ROOT / "data" / "нийт.xlsx"
OUT   = ROOT / "data" / "stock.json"

BRANCH_MAP = {
    "Очир салбар": {
        "Жижиг бараа": ["Очир хотхон", "Очир том сэлбэг"],
        "Том бараа":   ["Очир хотхон том"],
    },
    "25 салбар": {
        "Жижиг бараа": ["25 салбар", "25 том сэлбэг"],
        "Том бараа":   ["25 салбар том"],
    },
    "Д1000 салбар": {
        "Жижиг бараа": ["Дэнжийн1000 салбар", "Дэнж1000 том сэлбэг"],
        "Том бараа":   ["Дэнжийн 1000 том", "Дэнж 1000 том хуучин"],
    },
    "Мишээл салбар": {
        "Жижиг бараа": ["Мишээл салбар"],
        "Том бараа":   ["Мишээл том"],
    },
    "Алтан-Орд салбар": {
        "Жижиг бараа": ["Алтан орд"],
        "Том бараа":   ["Altanord tom"],
    },
    "Чулуун овоо салбар": {
        "Жижиг бараа": ["Салбар нарантуул"],
        "Том бараа":   ["Чулуун овоо том"],
    },
}

# Each warehouse gets its own slot so frontend can show combined or expanded
WAREHOUSE_NAMES = {
    "Жижиг бараа": ["Агуулах", "Агуулах - 2", "Агуулах жижиг 4", "Агуулах-3"],
    "Том бараа":   ["агуулах tom 1", "Агуулах том  2", "Нөөц агуулах"],
}

# Display labels for warehouses
WAREHOUSE_LABELS = {
    "Жижиг бараа": {
        "Агуулах":        "Агуулах 1",
        "Агуулах - 2":    "Агуулах 2",
        "Агуулах жижиг 4":"Агуулах 4",
        "Агуулах-3":      "Агуулах 3",
    },
    "Том бараа": {
        "агуулах tom 1":  "Агуулах Том 1",
        "Агуулах том  2": "Агуулах Том 2",
        "Нөөц агуулах":   "Нөөц агуулах",
    },
}

TYPE_KEY = {"Жижиг бараа": "жижиг", "Том бараа": "том"}


def load_df():
    print(f"Reading {EXCEL} …")
    df = pd.read_excel(EXCEL)
    df["Тоо"]         = pd.to_numeric(df["Тоо"], errors="coerce").fillna(0)
    df["Барааны код"]  = df["Барааны код"].fillna("").astype(str).str.strip()
    df["Барааны нэр"]  = df["Барааны нэр"].fillna("Тодорхойгүй").astype(str).str.strip()
    df["Салбар"]       = df["Салбар"].astype(str).str.strip()
    # Normalize Байршил to standard values regardless of caps
    байршил_map = {
        "том бараа": "Том бараа", "ТОМ БАРАА": "Том бараа", "Том Бараа": "Том бараа",
        "жижиг бараа": "Жижиг бараа", "ЖИЖИГ БАРАА": "Жижиг бараа", "Жижиг Бараа": "Жижиг бараа",
    }
    df["Байршил"] = df["Байршил"].fillna("").astype(str).str.strip().replace(байршил_map)
    # Optional columns — gracefully default to empty string
    # Ангилал — normalize to title-case to merge duplicates like 'бусад'/'Бусад'
    if "Ангилал" not in df.columns:
        df["Ангилал"] = ""
    df["Ангилал"] = (df["Ангилал"].fillna("").astype(str).str.strip()
                     .str.title()
                     .replace({"Ирэхгүй": "", "0": ""}))

    # Subcategory column may be "Дэд ангилал" or "дэд ангилал"
    sub_col = next((c for c in df.columns if c.lower() == "дэд ангилал"), None)
    if sub_col:
        df["Дэд ангилал"] = (df[sub_col].fillna("").astype(str).str.strip()
                              .replace({"0": "", "nan": ""}))
        if sub_col != "Дэд ангилал":
            df = df.drop(columns=[sub_col])
    else:
        df["Дэд ангилал"] = ""
    return df


def build_missing(df):
    result = {}
    for item_type_mn, type_key in TYPE_KEY.items():
        result[type_key] = {}
        type_df   = df[df["Байршил"] == item_type_mn]
        wh_names  = WAREHOUSE_NAMES[item_type_mn]
        wh_labels = WAREHOUSE_LABELS[item_type_mn]
        wh_df     = type_df[type_df["Салбар"].isin(wh_names)]

        # Per-warehouse quantities for every item
        wh_pivot = (
            wh_df.groupby(["Барааны код", "Барааны нэр", "Ангилал", "Дэд ангилал", "Салбар"])["Тоо"]
            .sum()
            .reset_index()
        )

        # Build item master: combined + per-warehouse breakdown
        item_wh = {}
        for _, row in wh_pivot.iterrows():
            code  = row["Барааны код"]
            label = wh_labels.get(row["Салбар"], row["Салбар"])
            if code not in item_wh:
                item_wh[code] = {
                    "код": code,
                    "нэр": row["Барааны нэр"],
                    "ангилал": row["Ангилал"],
                    "дэд": row["Дэд ангилал"],
                    "агуулах_нийт": 0,
                    "агуулах_дэлгэрэнгүй": {},
                }
            item_wh[code]["агуулах_нийт"]              += row["Тоо"]
            item_wh[code]["агуулах_дэлгэрэнгүй"][label] = \
                item_wh[code]["агуулах_дэлгэрэнгүй"].get(label, 0) + row["Тоо"]

        wh_items = {c for c, v in item_wh.items() if v["агуулах_нийт"] > 0}

        for branch_name, branch_data in BRANCH_MAP.items():
            raw_names  = branch_data.get(item_type_mn, [])
            branch_df  = type_df[type_df["Салбар"].isin(raw_names)]
            branch_agg = (
                branch_df.groupby("Барааны код")["Тоо"].sum().reset_index()
            )
            branch_items = set(branch_agg[branch_agg["Тоо"] > 0]["Барааны код"])

            missing_codes = wh_items - branch_items
            missing = [item_wh[c] for c in missing_codes if c in item_wh]
            # Sort by name for consistency
            missing.sort(key=lambda r: r["нэр"])

            result[type_key][branch_name] = missing
            print(f"  {type_key} / {branch_name}: {len(missing)} missing items")

    return result


def build_imbalance(df):
    result = {}
    for item_type_mn, type_key in TYPE_KEY.items():
        type_df  = df[df["Байршил"] == item_type_mn]
        wh_names = WAREHOUSE_NAMES[item_type_mn]
        wh_labels = WAREHOUSE_LABELS[item_type_mn]
        all_items = (
            type_df[["Барааны код", "Барааны нэр", "Ангилал", "Дэд ангилал"]]
            .drop_duplicates(subset=["Барааны код"])
            .query("`Барааны код` != ''")
        )

        rows = []
        for _, item_row in all_items.iterrows():
            code     = item_row["Барааны код"]
            name     = item_row["Барааны нэр"]
            ангилал  = item_row["Ангилал"]
            дэд      = item_row["Дэд ангилал"]
            item_df  = type_df[type_df["Барааны код"] == code]

            branch_stocks = {}
            total_branch  = 0
            for branch_name, branch_data in BRANCH_MAP.items():
                raw = branch_data.get(item_type_mn, [])
                qty = float(item_df[item_df["Салбар"].isin(raw)]["Тоо"].sum())
                branch_stocks[branch_name] = qty
                total_branch += qty

            # Per-warehouse breakdown
            wh_breakdown = {}
            wh_total = 0
            for wh_raw in wh_names:
                qty = float(item_df[item_df["Салбар"] == wh_raw]["Тоо"].sum())
                label = wh_labels.get(wh_raw, wh_raw)
                wh_breakdown[label] = qty
                wh_total += qty

            total = total_branch + wh_total
            if total == 0:
                continue

            # Rule 1: warehouse must be <=10% of total stock
            # (if warehouse is large, the missing-items panel handles supply — skip here)
            if total > 0 and wh_total / total > 0.10:
                continue

            # Rule 2: one branch holds >=70% of branch-only stock
            is_imbalanced = False
            if total_branch > 1:
                for qty in branch_stocks.values():
                    if qty / total_branch >= 0.70:
                        is_imbalanced = True
                        break

            if is_imbalanced:
                dominant = max(branch_stocks, key=lambda b: branch_stocks[b])
                rows.append({
                    "код": code, "нэр": name,
                    "ангилал": ангилал, "дэд": дэд,
                    **{b: branch_stocks[b] for b in BRANCH_MAP.keys()},
                    "агуулах_нийт": wh_total,
                    "агуулах_дэлгэрэнгүй": wh_breakdown,
                    "салбар_нийт": total_branch,
                    "нийт": total,
                    "давамгай": dominant,
                })

        result[type_key] = rows
        print(f"  {type_key} imbalanced: {len(rows)} items")

    return result


def build_meta(df):
    """Collect all unique categories/subcategories per item type."""
    meta = {}
    for item_type_mn, type_key in TYPE_KEY.items():
        type_df = df[df["Байршил"] == item_type_mn]
        cats    = sorted(set(type_df["Ангилал"].dropna().unique()) - {""})
        # subcategory → parent category mapping
        sub_map = {}
        for _, row in type_df[["Ангилал","Дэд ангилал"]].drop_duplicates().iterrows():
            cat = row["Ангилал"]
            sub = row["Дэд ангилал"]
            if sub and sub != "":
                sub_map.setdefault(cat, [])
                if sub not in sub_map[cat]:
                    sub_map[cat].append(sub)
        for cat in sub_map:
            sub_map[cat].sort()
        meta[type_key] = {
            "categories": cats,
            "subcategories": sub_map,
            "warehouses": list(WAREHOUSE_LABELS[item_type_mn].values()),
        }
    return meta


def main():
    if not EXCEL.exists():
        print(f"ERROR: {EXCEL} not found", file=sys.stderr)
        sys.exit(1)

    df = load_df()
    print("Building missing-items data …")
    missing = build_missing(df)
    print("Building imbalance data …")
    imbalance = build_imbalance(df)
    print("Building meta …")
    meta = build_meta(df)

    payload = {
        "missing":   missing,
        "imbalance": imbalance,
        "meta":      meta,
        "branches":  list(BRANCH_MAP.keys()),
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    size_kb = OUT.stat().st_size // 1024
    print(f"\n✅  Written {OUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
