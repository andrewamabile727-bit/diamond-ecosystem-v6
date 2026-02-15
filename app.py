import streamlit as st
import pandas as pd
import re
import io

# --- 1. ENGINE V6.1 (THE BRAIN) ---
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

def alpha_to_pos(s):
    if pd.isna(s) or str(s).strip() == '': return 1
    s = str(s).strip().upper()
    if s.isdigit(): return int(s)
    if s[0].isalpha(): return ord(s[0]) - ord('A') + 1
    return 1

# --- 2. APP CONFIGURATION ---
st.set_page_config(page_title="Diamond Ecosystem v6.1", layout="wide")
st.title("💎 Diamond Ecosystem v6.1")
st.markdown("### Manufacturing BOM Master Control")

category = st.sidebar.selectbox("Category Navigation", [
    "0: Master Sku", "1: Base Assy Kit", "2: Countertop Assy Kit",
    "3: Cladding Assy Kit", "4: Finish Kit", "5: Cladding Assy",
    "6: Cladding Panel", "7: Backer Board", "8: Countertop", "9: Frame"
])

# --- 3. DYNAMIC LOGIC MAPPING ---
def process_data(df, category_name):
    prefix = category_name.split(":")[0]
    col_out = category_name.split(": ")[1]
    
    # Required Column: Level 0 has 4 inputs, all others use 'MasterCode'
    required_cols = ['Base Assy Kit', 'Countertop Assy Kit', 'Cladding Assy Kit', 'Finish Kit'] if prefix == "0" else ['MasterCode']
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Missing required columns: {', '.join(missing)}")
        return None

    def get_id(row):
        try:
            code = str(row.get('MasterCode', '')).upper().strip()
            seg = [s.strip() for s in code.split('-')]
            
            # --- CATEGORY 0: MASTER SKU ---
            if prefix == "0":
                base, top = str(row.get('Base Assy Kit', '')), str(row.get('Countertop Assy Kit', ''))
                clad, fin = str(row.get('Cladding Assy Kit', '')), str(row.get('Finish Kit', ''))
                n2_val = base[1] if len(base) > 1 else '0'
                return f"0{n2_val}{poly_hash_v6(base + top + clad + fin)}-01"
            
            # --- CATEGORY 1, 2, 3: KIT LOGIC ---
            elif prefix in ["1", "2", "3"]:
                match = re.search(r'\d(\d)', code)
                n2_val = match.group(1) if match else "0"
                return f"{prefix}{n2_val}{poly_hash_v6(code)}-01"
            
            # --- CATEGORY 4: FINISH KIT ---
            elif prefix == "4":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"4{n2_val}{poly_hash_v6(code)}-01"

            # --- CATEGORY 5: CLADDING ASSY (V6.1 UPDATED) ---
            elif prefix == "5":
                # Input: O-61025-01-71815-01 -> Cleaned: 61025017181501
                # This matches the original 'Panel + Backer' DNA perfectly.
                if code.startswith('O-'):
                    cleaned_code = code[2:].replace("-", "")
                    n2_val = cleaned_code[1] if len(cleaned_code) > 1 else '0'
                    return f"5{n2_val}{poly_hash_v6(cleaned_code)}-01"
                return "FORMAT ERROR: Start with O-"
            
            # --- CATEGORY 6, 7: COMPONENTS ---
            elif prefix in ["6", "7"]:
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"{prefix}{n2_val}{poly_hash_v6(''.join(seg[:4]))}-01"

            # --- CATEGORY 8: COUNTERTOP ---
            elif prefix == "8":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"8{n2_val}{poly_hash_v6(''.join(seg[:3]))}-01"
            
            # --- CATEGORY 9: FRAME ---
            elif prefix == "9":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                fp = poly_hash_v6("".join(seg[:4]))
                rev = alpha_to_pos(seg[4]) if len(seg) > 4 else 1
                return f"9{n2_val}{fp}-{rev:02d}"

            return "UNKNOWN"
        except Exception: return "ERROR"

    df[col_out] = df.apply(get_id, axis=1)
    return df

# --- 4. USER WORKFLOW ---
uploaded_file = st.file_uploader(f"Upload CSV for {category}", type="csv")

if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
    if st.button("🚀 Generate Diamond IDs"):
        result_df = process_data(input_df, category)
        if result_df is not None:
            st.success(f"✅ Version 6.1 Active: {category} processed successfully.")
            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Processed CSV", csv, f"{category.replace(':','_')}_v6.1.csv", "text/csv")
