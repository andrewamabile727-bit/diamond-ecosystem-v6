import streamlit as st
import pandas as pd
import re
import io

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

def alpha_to_pos(s):
    if pd.isna(s) or str(s).strip() == '': return 1
    s = str(s).strip().upper()
    if s.isdigit(): return int(s)
    if s[0].isalpha(): return ord(s[0]) - ord('A') + 1
    return 1

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
    
    # Required Column Mapping
    required_cols = {
        "0": ['Base Assy Kit', 'Countertop Assy Kit', 'Cladding Assy Kit', 'Finish Kit'],
        "5": ['Cladding Panel', 'Backer Board']
    }.get(prefix, ['MasterCode'])
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Missing required columns: {', '.join(missing)}")
        return None

    def get_id(row):
        try:
            code = str(row.get('MasterCode', '')).upper()
            seg = [s.strip() for s in code.split('-')]
            
            # --- CATEGORY 0: MASTER SKU ---
            if prefix == "0":
                base = str(row.get('Base Assy Kit', ''))
                top = str(row.get('Countertop Assy Kit', ''))
                clad = str(row.get('Cladding Assy Kit', ''))
                fin = str(row.get('Finish Kit', ''))
                n2_val = base[1] if len(base) > 1 else '0'
                return f"0{n2_val}{poly_hash_v6(base + top + clad + fin)}-01"
            
            # --- CATEGORY 1, 2, 3: KIT LOGIC (Matches Colab Regex) ---
            elif prefix in ["1", "2", "3"]:
                # Colab uses: re.search(r'\d(\d)', code)
                match = re.search(r'\d(\d)', code)
                n2_val = match.group(1) if match else "0"
                return f"{prefix}{n2_val}{poly_hash_v6(code)}-01"
            
            # --- CATEGORY 4: FINISH KIT ---
            elif prefix == "4":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"4{n2_val}{poly_hash_v6(code)}-01"

            # --- CATEGORY 5: CLADDING ASSY ---
            elif prefix == "5":
                panel = str(row.get('Cladding Panel', ''))
                backer = str(row.get('Backer Board', ''))
                n2_val = panel[1] if len(panel) > 1 else '0'
                return f"5{n2_val}{poly_hash_v6(panel + backer)}-01"
            
            # --- CATEGORY 8: COUNTERTOP (Uses 3 Segments) ---
            elif prefix == "8":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"8{n2_val}{poly_hash_v6(''.join(seg[:3]))}-01"
            
            # --- CATEGORY 9: FRAME (Uses Rev Logic) ---
            elif prefix == "9":
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                fp = poly_hash_v6("".join(seg[:4]))
                rev = alpha_to_pos(seg[4]) if len(seg) > 4 else 1
                return f"9{n2_val}{fp}-{rev:02d}"

            # --- CATEGORY 6, 7: COMPONENTS (Uses 4 Segments) ---
            elif prefix in ["6", "7"]:
                n2_val = extract_n2(seg[1]) if len(seg) > 1 else 0
                return f"{prefix}{n2_val}{poly_hash_v6(''.join(seg[:4]))}-01"
            
            return "UNKNOWN"
        except Exception: return "ERROR"

    df[col_out] = df.apply(get_id, axis=1)
    return df

# --- 4. WORKFLOW ---
uploaded_file = st.file_uploader(f"Upload CSV for {category}", type="csv")

if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
    if st.button("🚀 Generate Diamond IDs"):
        result_df = process_data(input_df, category)
        if result_df is not None:
            st.success("✅ Logic Fully Synchronized with Colab History!")
            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Processed CSV", csv, f"{category}_Export.csv", "text/csv")
