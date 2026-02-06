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
    
    # Check for required columns before starting
    required_cols = {
        "0": ['Base Assy Kit', 'Countertop Assy Kit', 'Cladding Assy Kit', 'Finish Kit'],
        "5": ['Cladding Panel', 'Backer Board']
    }.get(prefix, ['MasterCode'])
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Missing required columns: {', '.join(missing)}")
        st.info("Please ensure your CSV headers match the names above exactly.")
        return None

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
                # Match Colab: Uses full MasterCode for these Kits
                return f"{prefix}{n2}{poly_hash_v6(code)}-01"
            
            elif prefix == "5":
                panel = str(row.get('Cladding Panel', ''))
                backer = str(row.get('Backer Board', ''))
                n2_val = panel[1] if len(panel) > 1 else '0'
                return f"5{n2_val}{poly_hash_v6(panel + backer)}-01"
            
            elif prefix == "8":
                # Match Colab: Countertop uses 3 segments
                return f"8{n2}{poly_hash_v6(''.join(seg[:3]))}-01"
            
            elif prefix in ["6", "7", "9"]:
                # Match Colab: Components use 4 segments
                return f"{prefix}{n2}{poly_hash_v6(''.join(seg[:4]))}-01"
            
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
            st.success("✅ IDs Generated and Matched to History!")
            st.dataframe(result_df)
            
            # THE RESTORED DOWNLOAD BUTTON
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Processed CSV",
                data=csv,
                file_name=f"{category.replace(':', '').replace(' ', '_')}_Export.csv",
                mime='text/csv',
            )
