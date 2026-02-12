import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict

# =========================
# SETTINGS
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6,8,10,12,14,16,18,20,22,25,32]

# =========================
# WEIGHT PER METER
# =========================
def weight_per_meter(d):
    return (d**2)/162

# =========================
# CUTTING OPTIMIZATION
# =========================
def optimize_cutting(lengths):
    best_solution=None
    min_waste=float("inf")
    min_bars=float("inf")
    for _ in range(ITERATIONS):
        shuffled=lengths[:]
        random.shuffle(shuffled)
        shuffled.sort(reverse=True)
        bars=[]
        for l in shuffled:
            placed=False
            for bar in bars:
                if sum(bar)+l<=BAR_LENGTH:
                    bar.append(l)
                    placed=True
                    break
            if not placed:
                bars.append([l])
        waste=sum(BAR_LENGTH - sum(bar) for bar in bars)
        if waste<min_waste or (waste==min_waste and len(bars)<min_bars):
            min_waste=waste
            min_bars=len(bars)
            best_solution=bars
    return best_solution

# =========================
# STREAMLIT INTERFACE
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton (USD)", min_value=0.0, value=1000.0)

st.markdown("## Enter Rebar Data")
data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length":0.0, "Quantity":0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1, col2 = st.columns(2)
            rows[i]["Length"] = col1.number_input(f"Length (m) [{i+1}] - Ø{d}", value=float(rows[i]["Length"]), key=f"len_{d}_{i}")
            rows[i]["Quantity"] = col2.number_input(f"Quantity [{i+1}] - Ø{d}", value=int(rows[i]["Quantity"]), min_value=0, key=f"qty_{d}_{i}")
        if st.button(f"Add Row Ø{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0, "Quantity":0})
            st.experimental_rerun()
        lengths_list = []
        for r in rows:
            lengths_list.extend([r["Length"]]*r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# =========================
# RUN OPTIMIZATION
# =========================
if st.button("Run Optimization"):
    results=[]
    waste_dict=defaultdict(lambda: {"count":0,"weight":0})
    purchase_data=[]
    for d,lengths in data.items():
        solution = optimize_cutting(lengths)
        total_required=sum(lengths)
        used_bars=len(solution)
        total_bar_length=used_bars*BAR_LENGTH
        wpm=weight_per_meter(d)
        required_weight=total_required*wpm
        used_weight=total_bar_length*wpm
        waste_weight=(total_bar_length - total_required)*wpm
        waste_percent=((total_bar_length - total_required)/total_bar_length)*100
        results.append([d, used_bars, used_weight, required_weight, waste_weight, waste_percent])
        for bar in solution:
            bar_total_length=sum(bar)
            bar_waste=BAR_LENGTH - bar_total_length
            if bar_waste>0:
                key=(d,round(bar_waste,6))
                waste_dict[key]["count"]+=1
                waste_dict[key]["weight"]+=bar_waste*wpm
        # Purchase summary uses total bars used and their total weight
        purchase_data.append([d, used_bars, used_weight])

    df=pd.DataFrame(results, columns=["Diameter","Bars Used","Used Weight (kg)","Required Weight (kg)","Waste Weight (kg)","Waste %"])
    waste_data=[]
    for (diameter,waste_length),info in waste_dict.items():
        waste_data.append([diameter, waste_length, info["count"], info["weight"]])
    waste_df=pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    purchase_df=pd.DataFrame(purchase_data, columns=["Diameter","Bars","Weight (kg)"])

    st.success("Optimization Completed Successfully ✅")
    st.markdown("### Main Report")
    st.dataframe(df)
    st.markdown("### Detailed Waste Report")
    st.dataframe(waste_df)
    st.markdown("### Purchase Summary (12m Bars)")
    st.dataframe(purchase_df)

    # =========================
    # GENERATE PDF
    # =========================
    from io import BytesIO
    pdf_file = generate_pdf(df, waste_df, purchase_df, price)
    with open(pdf_file, "rb") as f:
        st.download_button(label="Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
