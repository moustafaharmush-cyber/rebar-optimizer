import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict

# =========================
# Settings
# =========================
BAR_LENGTH = 12.0
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]
ITERATIONS = 3000

# =========================
# Weight per meter
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# Cutting Optimization
# =========================
def optimize_cutting(lengths, iterations=ITERATIONS):
    best_solution = None
    min_waste = float("inf")
    min_bars = float("inf")
    for _ in range(iterations):
        shuffled = lengths[:]
        random.shuffle(shuffled)
        shuffled.sort(reverse=True)
        bars = []
        for length in shuffled:
            placed = False
            for bar in bars:
                if sum(bar) + length <= BAR_LENGTH:
                    bar.append(length)
                    placed = True
                    break
            if not placed:
                bars.append([length])
        waste = sum(BAR_LENGTH - sum(bar) for bar in bars)
        if waste < min_waste or (waste == min_waste and len(bars) < min_bars):
            min_waste = waste
            min_bars = len(bars)
            best_solution = bars
    return best_solution

# =========================
# PDF Generator
# =========================
def generate_pdf(df, waste_df, purchase_df, detailed_waste_df):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # ----------------------
    # Main Report Table (no cost)
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Main Report", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_main = [25, 25, 35, 35, 35, 25]
    headers_main = ["Diameter", "Bars Used", "Required W (kg)", "Used W (kg)",
                    "Waste W (kg)", "Waste %"]
    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_required_weight = 0
    total_used_weight = 0
    total_waste_weight = 0

    for _, row in df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_main[1], 8, f"{int(row['Bars Used'])}", border=1, align="C")
        pdf.cell(col_widths_main[2], 8, f"{row['Required Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[3], 8, f"{row['Used Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[4], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[5], 8, f"{row['Waste %']:.2f}", border=1, align="C")
        pdf.ln()
        total_required_weight += row['Required Weight (kg)']
        total_used_weight += row['Used Weight (kg)']
        total_waste_weight += row['Waste Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_main[0]+col_widths_main[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_main[2], 8, f"{total_required_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{total_used_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[4], 8, f"{total_waste_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[5], 8, "", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Detailed Waste Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Detailed Waste per Diameter", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_detail = [25, 35, 25, 35]
    headers_detail = ["Diameter", "Waste Length (m)", "Number of Bars", "Weight (kg)"]
    for i, header in enumerate(headers_detail):
        pdf.cell(col_widths_detail[i], 8, header, border=1, align="C")
    pdf.ln()

    total_detailed_waste_weight = 0
    for _, row in detailed_waste_df.iterrows():
        pdf.cell(col_widths_detail[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_detail[1], 8, f"{row['Waste Length (m)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_detail[2], 8, f"{int(row['Number of Bars'])}", border=1, align="C")
        pdf.cell(col_widths_detail[3], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
        total_detailed_waste_weight += row['Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_detail[0]+col_widths_detail[1]+col_widths_detail[2], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_detail[3], 8, f"{total_detailed_waste_weight:.2f}", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Purchase Summary Table (with cost)
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Purchase Summary (12m Bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_purchase = [25, 35, 35, 30]
    headers_purchase = ["Diameter", "Number of Bars", "Weight (kg)", "Cost ($)"]
    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()

    total_purchase_weight = 0
    total_purchase_cost = 0
    for _, row in purchase_df.iterrows():
        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_purchase[3], 8, f"{row['Cost']:.2f}", border=1, align="C")
        pdf.ln()
        total_purchase_weight += row['Weight (kg)']
        total_purchase_cost += row['Cost']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_purchase[0]+col_widths_purchase[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_purchase[2], 8, f"{total_purchase_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_purchase[3], 8, f"{total_purchase_cost:.2f}", border=1, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename

# =========================
# Streamlit Interface
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

# Price input
price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# Input Data
data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length": 0.0, "Quantity": 0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1, col2 = st.columns(2)
            rows[i]["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=float(rows[i]["Length"]), key=f"len_{d}_{i}")
            rows[i]["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=int(rows[i]["Quantity"]), min_value=0, key=f"qty_{d}_{i}")
        if st.button(f"Add Row Ø{d}"):
            st.session_state[f"rows_{d}"].append({"Length": 0.0, "Quantity": 0})
            st.rerun()
        lengths_list = []
        for r in rows:
            lengths_list.extend([r["Length"]] * r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# =========================
# Run Optimization Button
# =========================
if st.button("Run Optimization"):
    results = []
    waste_dict = defaultdict(lambda: {"count":0, "weight":0})
    purchase_list = []
    detailed_waste_data = []

    for d, lengths in data.items():
        solution = optimize_cutting(lengths)
        if not solution:
            continue
        total_required = sum(lengths)
        used_bars = len(solution)
        total_bar_length = used_bars * BAR_LENGTH
        wpm = weight_per_meter(d)
        required_weight = total_required * wpm
        used_weight = total_bar_length * wpm
        waste_weight = (total_bar_length - total_required) * wpm
        waste_percent = ((total_bar_length - total_required)/total_bar_length)*100
        cost = (used_weight/1000)*price
        results.append([d, used_bars, required_weight, used_weight, waste_weight, waste_percent, cost])

        # Detailed Waste Data
        for bar in solution:
            bar_total_length = sum(bar)
            bar_waste = BAR_LENGTH - bar_total_length
            if bar_waste > 0:
                detailed_waste_data.append([d, bar_waste, 1, bar_waste*wpm])

        # Purchase summary
        purchase_list.append([d, used_bars, used_weight, cost])

    df = pd.DataFrame(results, columns=["Diameter","Bars Used","Required Weight (kg)","Used Weight (kg)","Waste Weight (kg)","Waste %","Cost"])
    detailed_waste_df = pd.DataFrame(detailed_waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Weight (kg)"])
    purchase_df = pd.DataFrame(purchase_list, columns=["Diameter","Bars","Weight (kg)","Cost"])

    st.success("Optimization Completed Successfully ✅")
    st.markdown("### Main Report")
    st.dataframe(df.style.format({"Required Weight (kg)":"{:.2f}","Used Weight (kg)":"{:.2f}","Waste Weight (kg)":"{:.2f}","Waste %":"{:.2f}"}))
    st.markdown("### Detailed Waste Table")
    st.dataframe(detailed_waste_df.style.format({"Waste Length (m)":"{:.2f}","Weight (kg)":"{:.2f}"}))
    st.markdown("### Purchase Summary")
    st.dataframe(purchase_df.style.format({"Weight (kg)":"{:.2f}","Cost":"{:.2f}"}))

    # Generate PDF
    pdf_file = generate_pdf(df, detailed_waste_df, purchase_df, detailed_waste_df)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
