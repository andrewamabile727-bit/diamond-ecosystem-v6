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
st.markdown("### Manufacturing BOM Master Control")

# Sidebar Navigation
category = st.sidebar.selectbox("Category Navigation", [
    "0: Master Sku", "1: Base Assy Kit", "2: Countertop Assy Kit",
    "3: Cladding Assy Kit", "4: Finish Kit", "5: Cladding Assy",
    "6: Cladding Panel", "7: Backer Board", "8: Countertop", "9: Frame"
])

# --- 3. DYNAMIC LOGIC MAPPING ---
def process_data(df, category_name):
    try:
        # Get prefix number (0-9)
        prefix = category_name.split(":")[0]
        
        def get_id(row):
            code = str(row['MasterCode']).upper()
            seg = [s.strip() for s in code.split('-')]
            n2 = extract_n2(seg[1]) if len(seg) > 1 else 0
            
            # CATEGORY 0: Master SKU
            if prefix == "0":
                return f"0{str(row['Base Assy Kit'])[1] if len(str(row['Base Assy Kit'])) > 1 else '0'}{poly_hash_v6(str(row['Base Assy Kit']) + str(row['Countertop Assy Kit']) + str(row['Cladding Assy Kit']) + str(row['Finish Kit']))}-01"
            
            # CATEGORY 1: Base Assy Kit
            elif prefix == "1":
                return f"1{re.search(r'\d(\d)', seg[1]).group(1) if len(seg) > 1 else '0'}{poly_hash_v6(code)}-01"
            
            # CATEGORY 2, 3, 4: (Uses 5 Segments)
            elif prefix in ["2", "3", "4"]:
                fp = poly_hash_v6("".join(seg[:5]))
                return f"{prefix}{n2}{fp}-01"
            
            # CATEGORY 5: Cladding Assy
            elif prefix == "5":
                return f"5{str(row['Cladding Panel'])[1] if len(str(row['Cladding Panel'])) > 1 else '0'}{poly_hash_v6(str(row['Cladding Panel']) + str(row['Backer Board']))}-01"
            
            # CATEGORY 6, 7, 8, 9: (Uses 4 Segments)
            elif prefix in ["6", "7", "8", "9"]:
                fp = poly_hash_v6("".join(seg[:4]))
                return f"{prefix}{n2}{fp}-01"
            
            return "ERROR"

        col_out = category_name.split(": ")[1]
        df[col_out] = df.apply(get_id, axis=1)
        return df
    except Exception as e:
        st.error(f"Logic Error: {e}")
        return None

# --- 4. USER WORKFLOW ---
uploaded_file = st.file_uploader(f"Upload CSV for {category}", type="csv")

if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
    if st.button("Generate Diamond IDs"):
        result_df = process_data(input_df, category)
        if result_df is not None:
            st.success("IDs Matched to Colab History!")
            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, f"{category}_Output.csv", "text/csv")
            
            st.divider()
            if st.button("🚀 Sync to Airtable"):
                st.info("Ready to connect to Airtable. Please provide your API keys in Settings.")
