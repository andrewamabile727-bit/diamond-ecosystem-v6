import streamlit as st
import pandas as pd
import re

# --- 1. ENGINE V6.0 (THE BRAIN) ---
def poly_hash_v6(string, modulo=1000):
    h = 0
    clean_str = str(string).upper().replace("-", "")
    for char in clean_str:
        h = (h * 53 + ord(char))
    h += len(clean_str)
    return f"{h % modulo:03d}"

def extract_n2(segment):
    nums = re.findall(r'\d+', str(segment))
    if nums:
        val = sum(int(n) for n in nums[:2])
        return val % 10
    return 0

# --- 2. APP CONFIGURATION ---
st.set_page_config(page_title="Diamond Ecosystem v6.0", layout="wide")
st.title("💎 Diamond Ecosystem v6.0")

category = st.sidebar.selectbox("Category Navigation", [
    "0: Master Sku", "1: Base Assy Kit", "2: Countertop Assy Kit",
    "3: Cladding Assy Kit", "4: Finish Kit", "5: Cladding Assy",
    "6: Cladding Panel", "7: Backer Board", "8: Countertop", "9: Frame"
])

# --- 3. DYNAMIC LOGIC MAPPING ---
def process_data(df, category_name):
    prefix = category_name.split(":")[0]
    col_out = category_name.split(": ")[1]
    
    def get_id(row):
        try:
            code = str(row.get('MasterCode', '')).upper()
            seg = [s.strip() for s in code.split('-')]
            n2 = extract_n2(seg[1]) if len(seg) > 1 else 0
            
            if prefix == "0":
                kits = [str(row.get(k, '')) for k in ['Base Assy Kit', 'Countertop Assy Kit', 'Cladding Assy Kit', 'Finish Kit']]
                n2_val = kits[0][1] if len(kits[0]) > 1 else '0'
                return f"0{n2_val}{poly_hash_v6(''.join(kits))}-01"
            
            elif prefix == "1":
                return f"1{re.search(r'\d(\d)', seg[1]).group(1) if len(seg) > 1 else '0'}{poly_hash_v6(code)}-01"
            
            elif prefix in ["2", "3", "4"]:
                # Colab logic for Kits uses 5 segments
                return f"{prefix}{n2}{poly_hash_v6(''.join(seg[:5]))}-01"
            
            elif prefix == "5":
                panel = str(row.get('Cladding Panel', ''))
                backer = str(row.get('Backer Board', ''))
                n2_val = panel[1] if len(panel) > 1 else '0'
                return f"5{n2_val}{poly_hash_v6(panel + backer)}-01"
            
            elif prefix == "8":
                # Special Rule for Countertop: Uses 3 segments
                return f"8{n2}{poly_hash_v6(''.join(seg[:3]))}-01"
            
            elif prefix in ["6", "7", "9"]:
                return f"{prefix}{n2}{poly_hash_v6(''.join(seg[:4]))}-01"
            
            return "UNKNOWN"
        except Exception: return "ERROR"

    # Check for required columns based on category
    required = {
        "0": ['Base Assy Kit', 'Countertop Assy Kit', 'Cladding Assy Kit', 'Finish Kit'],
        "5": ['Cladding Panel', 'Backer Board']
    }.get(prefix, ['MasterCode'])
    
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing Columns in CSV: {', '.join(missing)}")
        return None

    df[col_out] = df.apply(get_id, axis=1)
    return df

# --- 4. WORKFLOW ---
uploaded_file = st.file_uploader(f"Upload CSV for {category}", type="csv")
if uploaded_file and st.button("Generate Diamond IDs"):
    result = process_data(pd.read_csv(uploaded_file), category)
    if result is not None:
        st.success("Logic Synchronized with Colab!")
        st.dataframe(result)
