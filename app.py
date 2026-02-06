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

def alpha_to_pos(s):
    if pd.isna(s) or str(s).strip() == '': return 1
    s = str(s).strip().upper()
    if s.isdigit(): return int(s)
    if s[0].isalpha(): return ord(s[0]) - ord('A') + 1
    return 1

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
st.sidebar.header("Select BOM Level")
category = st.sidebar.selectbox("Category Navigation", [
    "0: Master Sku",
    "1: Base Assy Kit",
    "2: Countertop Assy Kit",
    "3: Cladding Assy Kit",
    "4: Finish Kit",
    "5: Cladding Assy",
    "6: Cladding Panel",
    "7: Backer Board",
    "8: Countertop",
    "9: Frame"
])

# --- 3. DYNAMIC LOGIC MAPPING ---
def process_data(df, category):
    try:
        if category == "0: Master Sku":
            df['Master Sku'] = df.apply(lambda x: f"0{str(x['Base Assy Kit'])[1] if len(str(x['Base Assy Kit'])) > 1 else '0'}{poly_hash_v6(str(x['Base Assy Kit']) + str(x['Countertop Assy Kit']) + str(x['Cladding Assy Kit']) + str(x['Finish Kit']))}-01", axis=1)
        
        elif category == "1: Base Assy Kit":
            df['Base Assy Kit'] = df['MasterCode'].apply(lambda x: f"1{re.search(r'\d(\d)', str(x).split('-')[1]).group(1) if '-' in str(x) else '0'}{poly_hash_v6(x)}-01")
            
        elif category == "5: Cladding Assy":
            df['Cladding Assy'] = df.apply(lambda x: f"5{str(x['Cladding Panel'])[1] if len(str(x['Cladding Panel'])) > 1 else '0'}{poly_hash_v6(str(x['Cladding Panel']) + str(x['Backer Board']))}-01", axis=1)
            
        # Logic for Levels 2, 3, 4, 6, 7, 8 (Standard Hash + Prefix)
        else:
            prefix = category.split(":")[0]
            col_name = category.split(": ")[1]
            df[col_name] = df['MasterCode'].apply(lambda x: f"{prefix}{extract_n2(str(x).split('-')[1]) if '-' in str(x) else '0'}{poly_hash_v6(x)}-01")
            
        return df
    except Exception as e:
        st.error(f"Mapping Error: Ensure your CSV column headers match the requirements. ({e})")
        return None

# --- 4. USER WORKFLOW ---
uploaded_file = st.file_uploader(f"Upload {category.split(': ')[1]}.csv", type="csv")

if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
    st.write("### Data Preview")
    st.dataframe(input_df.head())
    
    if st.button("Generate Diamond IDs"):
        result_df = process_data(input_df, category)
        
        if result_df is not None:
            st.success("IDs Generated Successfully!")
            st.dataframe(result_df)
            
            # Download Button
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Processed CSV",
                data=csv,
                file_name=f"{category.replace(':', '').replace(' ', '_')}_Output.csv",
                mime='text/csv',
            )
            
            # Placeholder for Airtable Sync
            st.divider()
            st.subheader("Cloud Integration")
            if st.button("🚀 Sync to Airtable"):
                st.info("Airtable API Connection detected. Ready for mapping.")
                # Future: pyairtable logic goes here