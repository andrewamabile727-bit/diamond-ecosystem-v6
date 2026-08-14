import streamlit as st
import pandas as pd
import re
import os
import datetime

st.set_page_config(page_title="BOM Pro v9.6", layout="wide")

# --- 1. HARDCODED FILENAMES ---
MASTER_FILE = "Item_Master_v4_Template.csv"
LINKS_FILE = "BOM_Links_v4_Template.csv"
SKU_FILE = "L0&L1 Skus..xlsx - Sheet1.csv"

# --- 2. UNCACHED DIRECT FILE LOAD ---
def load_data():
    if not all(os.path.exists(f) for f in [MASTER_FILE, LINKS_FILE, SKU_FILE]):
        return None, None, None

    # Load CSVs and strip whitespace from text cells
    df_m = pd.read_csv(MASTER_FILE, encoding='utf-8-sig').apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df_l = pd.read_csv(LINKS_FILE, encoding='utf-8-sig').apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df_s = pd.read_csv(SKU_FILE, encoding='utf-8-sig').apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Clean header titles and remove ghost columns created by Excel
    for df in [df_m, df_l, df_s]:
        df.columns = [str(c).strip() for c in df.columns]
        df.drop(columns=[c for c in df.columns if 'Unnamed' in c or c == ''], inplace=True, errors='ignore')

    # Convert Unit Cost to clean floats
    cost_col = next((c for c in df_m.columns if "Cost" in c), "Unit Cost")
    df_m['Math_Cost'] = df_m[cost_col].replace(r'[^\d.]', '', regex=True).replace('', '0').astype(float)
    
    return df_m, df_l, df_s

# --- 3. INITIALIZE & DIAGNOSTIC HEADER ---
st.title("🚀 BOM Professional v9.6")

df_m, df_l, df_s = load_data()

if df_m is None:
    st.error(f"🚨 Missing core CSV files! Ensure `{MASTER_FILE}`, `{LINKS_FILE}`, and `{SKU_FILE}` exist in your root GitHub repository folder.")
    st.stop()

# --- DIAGNOSTIC DEBUG BANNER ---
mtime = os.path.getmtime(MASTER_FILE)
mod_time_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

k39_row = df_m[df_m['Part No.'].astype(str).str.strip() == 'K39476']
k39_cost_val = f"${k39_row['Math_Cost'].values[0]:,.2f}" if not k39_row.empty else "NOT FOUND"
k39_desc_val = k39_row['Part Description'].values[0] if not k39_row.empty else "NOT FOUND"

st.warning(f"🔍 **DEBUG BAR v9.6** | Server File Date: `{mod_time_str}` | K39476 Cost: `{k39_cost_val}` | Description: `{k39_desc_val}`")

# Fast lookup dictionaries
master_map = df_m.set_index('Part No.').to_dict('index')

bom_tree = {}
for _, row in df_l.iterrows():
    parent = str(row.iloc[0]) # Parent Part
    if parent not in bom_tree: 
        bom_tree[parent] = []
    bom_tree[parent].append({
        'id': str(row.iloc[1]), # Child Part
        'qty': pd.to_numeric(row.iloc[2], errors='coerce') or 1.0, # Quantity
        'uom': str(row.iloc[3]) if len(row) > 3 else "Ea." # Unit of Measure
    })

# --- 4. NAVIGATION & SELECTION ---
st.sidebar.header("Navigation")
nav_type = st.sidebar.radio("View Depth", ["Top Level (SKU List)", "Sub-Assemblies (All Parents)"])

cols = df_s.columns.tolist()
cat_map = {
    "Saleable SKUs": ("Saleable Sku", "Saleable Sku Description"),
    "Base Assemblies": ("Base Assy Kit", "Base Assy Kit Description"),
    "Countertops": ("Countertop Assy Kit", "Countertop Assy Kit Description"),
    "Cladding": ("Cladding Assy Kit", "Cladding Assy Kit Description"),
    "Finish Kits": ("Finish Kit", "Finish Kit Description")
}

if nav_type == "Top Level (SKU List)":
    available_cats = [k for k, v in cat_map.items() if v[0] in cols]
    mode = st.selectbox("Category", available_cats)
    id_col, desc_col = cat_map[mode]
    
    options = []
    valid_rows = df_s[df_s[id_col].notna() & (df_s[id_col] != "")]
    for _, r in valid_rows.drop_duplicates(subset=[id_col]).iterrows():
        options.append(f"{r[id_col]} | {r.get(desc_col, 'N/A')}")
    selection = st.selectbox(f"Select {mode}", ["-- Select --"] + sorted(options))

else:
    sub_options = []
    for p_id in sorted(bom_tree.keys()):
        p_desc = master_map.get(p_id, {}).get('Part Description', 'N/A')
        sub_options.append(f"{p_id} | {p_desc}")
    selection = st.selectbox("Select Sub-Assembly", ["-- Select --"] + sub_options)

# --- 5. CALCULATION & EXPORT ENGINE ---
if selection != "-- Select --":
    sel_id = selection.split(" | ")[0].strip()
    sel_name = selection.split(" | ")[1].strip()

    final_bom = []
    def explode(pid, depth=1, mult=1):
        if depth > 12: return
        for child in bom_tree.get(pid, []):
            cid = child['id']
            t_qty = mult * child['qty']
            meta = master_map.get(cid, {})
            
            final_bom.append({
                'Level': depth,
                'Part No.': cid,
                'Description': meta.get('Part Description', 'N/A'),
                'Total Qty': t_qty,
                'UOM': child['uom'],
                'Unit Cost': meta.get('Math_Cost', 0.0),
                'Ext. Cost': meta.get('Math_Cost', 0.0) * t_qty
            })
            explode(cid, depth + 1, t_qty)

    explode(sel_id)

    if final_bom:
        res_df = pd.DataFrame(final_bom)
        st.metric("Total Roll-up Cost", f"${res_df['Ext. Cost'].sum():,.2f}")
        
        # Display Table on Screen
        disp = res_df.copy()
        disp['Unit Cost'] = disp['Unit Cost'].map("${:,.2f}".format)
        disp['Ext. Cost'] = disp['Ext. Cost'].map("${:,.2f}".format)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        
        # CSV Export with Single-Cell Header (Name, Number in Cell A1)
        csv_header = f'"{sel_name}, {sel_id}"\n\n'
        csv_body = res_df.to_csv(index=False)
        st.download_button("📥 Download CSV", (csv_header + csv_body).encode('utf-8-sig'), f"BOM_{sel_id}.csv")
    else:
        st.warning(f"No components found for '{sel_id}'. Verify that this ID is listed in the 'Parent Part' column of `{LINKS_FILE}`.")