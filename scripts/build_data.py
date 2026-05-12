#!/usr/bin/env python3
"""
Convert нийт.xlsx → data/stock.json
Columns: Салбар, Барааны код, Барааны нэр, Тоо, Байршил, Ангилал, дэд ангилал
Optional: Гарал үүсэл (origin)
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
        "жижиг":  ["Очир хотхон", "Очир том сэлбэг"],
        "том":    ["Очир хотхон том"],
        "сэлбэг": ["Очир хотхон", "Очир том сэлбэг", "Очир хотхон том"],
    },
    "25 салбар": {
        "жижиг":  ["25 салбар", "25 том сэлбэг"],
        "том":    ["25 салбар том"],
        "сэлбэг": ["25 салбар", "25 том сэлбэг", "25 салбар том"],
    },
    "Д1000 салбар": {
        "жижиг":  ["Дэнжийн1000 салбар", "Дэнж1000 том сэлбэг"],
        "том":    ["Дэнжийн 1000 том", "Дэнж 1000 том хуучин"],
        "сэлбэг": ["Дэнжийн1000 салбар", "Дэнж1000 том сэлбэг", "Дэнжийн 1000 том"],
    },
    "Мишээл салбар": {
        "жижиг":  ["Мишээл салбар"],
        "том":    ["Мишээл том"],
        "сэлбэг": ["Мишээл салбар", "Мишээл том"],
    },
    "Алтан-Орд салбар": {
        "жижиг":  ["Алтан орд"],
        "том":    ["Altanord tom"],
        "сэлбэг": ["Алтан орд"],
    },
    "Чулуун овоо салбар": {
        "жижиг":  ["Салбар нарантуул"],
        "том":    ["Чулуун овоо том"],
        "сэлбэг": ["Салбар нарантуул", "Чулуун овоо том"],
    },
}

WAREHOUSE_NAMES = {
    "жижиг":  ["Агуулах", "Агуулах жижиг 2 Цогтгэрэл", "Агуулах жижиг 4", "Агуулах-3"],
    "том":    ["агуулах tom 1", "Агуулах том  2", "Нөөц агуулах"],
    "сэлбэг": ["Агуулах", "Агуулах жижиг 2 Цогтгэрэл", "Агуулах-3", "агуулах tom 1", "Нөөц агуулах"],
}

WAREHOUSE_LABELS = {
    "жижиг": {
        "Агуулах": "Агуулах 1", "Агуулах жижиг 2 Цогтгэрэл": "Агуулах 2",
        "Агуулах жижиг 4": "Агуулах 4", "Агуулах-3": "Агуулах 3",
    },
    "том": {
        "агуулах tom 1": "Агуулах Том 1", "Агуулах том  2": "Агуулах Том 2",
        "Нөөц агуулах": "Нөөц агуулах",
    },
    "сэлбэг": {
        "Агуулах": "Агуулах 1", "Агуулах жижиг 2 Цогтгэрэл": "Агуулах 2",
        "Агуулах-3": "Агуулах 3", "агуулах tom 1": "Агуулах Том 1",
        "Нөөц агуулах": "Нөөц агуулах",
    },
}

EXCLUDE_SALBAR = {"бичиг хэрэг", "Мабуд бэлэн бүтээгдэхүүн"}
ALL_TYPES = ["жижиг", "том", "сэлбэг"]
# Map Байршил to type key — case-insensitive
EXCLUDE_БАЙРШИЛ = {"хангамж", "кодгүй"}
def байршил_to_type(v):
    v = str(v).strip().lower()
    if v in EXCLUDE_БАЙРШИЛ: return ""
    if "жижиг" in v: return "жижиг"
    if "сэлбэг" in v: return "сэлбэг"
    if "том" in v:   return "том"
    return ""



def load_df():
    print(f"Reading {EXCEL} …")
    # Read Sheet1 explicitly — file may have multiple sheets
    xl = pd.ExcelFile(EXCEL)
    sheet = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[-1]
    df = pd.read_excel(EXCEL, sheet_name=sheet)
    df["Тоо"]        = pd.to_numeric(df["Тоо"], errors="coerce").fillna(0)
    df["Барааны код"] = df["Барааны код"].fillna("").astype(str).str.strip()
    df["Барааны нэр"] = df["Барааны нэр"].fillna("Тодорхойгүй").astype(str).str.strip()
    df["Салбар"]      = df["Салбар"].astype(str).str.strip()
    df["Байршил"]     = df["Байршил"].fillna("").astype(str).str.strip()

    cat_col = next((c for c in df.columns if c.lower() == "ангилал"), None)
    sub_col = next((c for c in df.columns if c.lower() == "дэд ангилал"), None)
    ori_col = next((c for c in df.columns if "гарал" in c.lower() or "origin" in c.lower()), None)
    # Fix: also accept #N/A strings in origin

    JUNK = {"0", "nan", "", "Nan", "Ирэхгүй", "ирэхгүй"}
    df["Ангилал"]     = (df[cat_col].fillna("").astype(str).str.strip().str.title()
                         .apply(lambda x: "" if x in JUNK else x)) if cat_col else ""
    df["Дэд ангилал"] = (df[sub_col].fillna("").astype(str).str.strip().str.title()
                         .apply(lambda x: "" if x in JUNK | {"Сэлбэг"} else x)) if sub_col else ""
    df["Гарал"]       = (df[ori_col].fillna("").astype(str).str.strip()
                         .apply(lambda x: "" if x.lower() in {"#n/a","nan","","#н/а"} else x)) if ori_col else ""

    df = df[~df["Салбар"].isin(EXCLUDE_SALBAR)]
    df["_type"] = df["Байршил"].apply(байршил_to_type)
    # Сэлбэг: also detect by Ангилал in case Байршил is жижиг/том
    df.loc[(df["_type"].isin(["жижиг","том"])) & (df["Ангилал"].str.upper() == "СЭЛБЭГ"), "_type"] = "сэлбэг"
    df = df[df["_type"].isin(ALL_TYPES) & (df["Барааны код"] != "")]
    return df


def build_missing(df):
    result = {}
    for tk in ALL_TYPES:
        result[tk] = {}
        tdf = df[df["_type"] == tk]
        wh_df = tdf[tdf["Салбар"].isin(WAREHOUSE_NAMES[tk])]
        wh_pivot = wh_df.groupby(
            ["Барааны код","Барааны нэр","Ангилал","Дэд ангилал","Гарал","Салбар"]
        )["Тоо"].sum().reset_index()

        item_wh = {}
        for _, row in wh_pivot.iterrows():
            code  = row["Барааны код"]
            label = WAREHOUSE_LABELS[tk].get(row["Салбар"], row["Салбар"])
            if code not in item_wh:
                item_wh[code] = {
                    "код": code, "нэр": row["Барааны нэр"],
                    "ангилал": row["Ангилал"], "дэд": row["Дэд ангилал"],
                    "гарал": row["Гарал"], "агуулах_нийт": 0, "агуулах_дэлгэрэнгүй": {},
                }
            item_wh[code]["агуулах_нийт"] += row["Тоо"]
            item_wh[code]["агуулах_дэлгэрэнгүй"][label] = (
                item_wh[code]["агуулах_дэлгэрэнгүй"].get(label, 0) + row["Тоо"])

        wh_items = {c for c, v in item_wh.items() if v["агуулах_нийт"] > 0}

        for branch, bdata in BRANCH_MAP.items():
            raw = bdata.get(tk, [])
            branch_df  = tdf[tdf["Салбар"].isin(raw)]
            branch_agg = branch_df.groupby("Барааны код")["Тоо"].sum().reset_index()
            have = set(branch_agg[branch_agg["Тоо"] > 0]["Барааны код"])
            missing = sorted([item_wh[c] for c in wh_items - have if c in item_wh], key=lambda r: r["нэр"])
            result[tk][branch] = missing
            print(f"  {tk} / {branch}: {len(missing)} missing")
    return result


def build_imbalance(df):
    result = {}
    for tk in ALL_TYPES:
        tdf = df[df["_type"] == tk]
        all_items = tdf[["Барааны код","Барааны нэр","Ангилал","Дэд ангилал","Гарал"]].drop_duplicates(subset=["Барааны код"])
        rows = []
        for _, ir in all_items.iterrows():
            code    = ir["Барааны код"]
            item_df = tdf[tdf["Барааны код"] == code]

            bs = {}; tb = 0
            for branch, bdata in BRANCH_MAP.items():
                qty = float(item_df[item_df["Салбар"].isin(bdata.get(tk,[]))]["Тоо"].sum())
                bs[branch] = qty; tb += qty

            wbd = {}; wt = 0
            for wraw in WAREHOUSE_NAMES[tk]:
                qty = float(item_df[item_df["Салбар"] == wraw]["Тоо"].sum())
                wbd[WAREHOUSE_LABELS[tk].get(wraw, wraw)] = qty; wt += qty

            total = tb + wt
            if total == 0: continue
            if wt / total > 0.10: continue

            imb = any(qty / tb >= 0.70 for qty in bs.values()) if tb > 1 else False
            if imb:
                rows.append({
                    "код": code, "нэр": ir["Барааны нэр"],
                    "ангилал": ir["Ангилал"], "дэд": ir["Дэд ангилал"], "гарал": ir["Гарал"],
                    **{b: bs[b] for b in BRANCH_MAP},
                    "агуулах_нийт": wt, "агуулах_дэлгэрэнгүй": wbd,
                    "салбар_нийт": tb, "нийт": total,
                    "давамгай": max(bs, key=lambda b: bs[b]),
                })
        result[tk] = rows
        print(f"  {tk} imbalanced: {len(rows)}")
    return result


def build_meta(df):
    meta = {}
    for tk in ALL_TYPES:
        tdf  = df[df["_type"] == tk]
        cats = sorted(set(tdf["Ангилал"].dropna().unique()) - {"", "Сэлбэг"})
        sub_map = {}
        for _, row in tdf[["Ангилал","Дэд ангилал"]].drop_duplicates().iterrows():
            cat, sub = row["Ангилал"], row["Дэд ангилал"]
            if cat and sub:
                sub_map.setdefault(cat, [])
                if sub not in sub_map[cat]: sub_map[cat].append(sub)
        for cat in sub_map: sub_map[cat].sort()
        origins = sorted(set(tdf["Гарал"].dropna().unique()) - {""})
        meta[tk] = {
            "categories": cats, "subcategories": sub_map,
            "warehouses": list(WAREHOUSE_LABELS[tk].values()),
            "origins": origins,
        }
    return meta


def main():
    if not EXCEL.exists():
        print(f"ERROR: {EXCEL} not found", file=sys.stderr); sys.exit(1)
    df = load_df()
    print(f"Loaded {len(df)} usable rows")
    for t in ALL_TYPES: print(f"  {t}: {len(df[df['_type']==t])} rows")
    print("\nBuilding missing-items …")
    missing   = build_missing(df)
    print("\nBuilding imbalance …")
    imbalance = build_imbalance(df)
    print("\nBuilding meta …")
    meta      = build_meta(df)
    payload   = {
        "missing": missing, "imbalance": imbalance, "meta": meta,
        "branches": list(BRANCH_MAP.keys()), "types": ALL_TYPES,
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",",":")))
    print(f"\n✅  Written {OUT}  ({OUT.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
