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
ITERATIONS = 3000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

# =========================
# Weight per meter
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# Cutting Optimization
# =========================
def optimize_cutting(lengths):
    best_solution = None
    min_waste = float("inf")
    min_bars = float("inf")
    for _ in range(ITERATIONS):
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
    return best_solution, waste

# =========================
# PDF Generator
# =========================
def generate_pdf(df, waste_df, purchase_df, price):
    pdf = FPDF(orientation='L')
    pdf.add_page()

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # ----------------------
    # Main Report Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Main Report", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_main = [25, 25, 35, 35, 35, 25, 30]
    headers_main = ["Diameter", "Bars Used", "Required W (kg)", "Used W (kg)",
                    "Waste W (kg)", "Waste %", "Cost ($)"]

    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_required_weight = 0
    total_used_weight = 0
    total_waste_weight = 0
    total_cost = 0

    for _, row in df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])}mm", border=1)
        pdf.cell(col_widths_main[1], 8, f"{int(row['Bars Used'])}", border=1)
        pdf.cell(col_widths_main[2], 8, f"{row['Required Weight (kg)']:.2f}", border=1)
        pdf.cell(col_widths_main[3], 8, f"{row['Used Weight (kg)']:.2f}", border=1)
        pdf.cell(col_widths_main[4], 8, f"{row['Waste Weight (kg)']:.2f}", border=1)
        pdf.cell(col_widths_main[5], 8, f"{row['Waste %']:.2f}", border=1)
        pdf.cell(col_widths_main[6], 8, f"{row['Cost']:.2f}", border=1)
        pdf.ln()
        total_required_weight += row['Required Weight (kg)']
        total_used_weight += row['Used Weight (kg)']
        total_waste_weight += row['Waste Weight (kg)']
        total_cost += row['Cost']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_main[0]+col_widths_main[1], 8, "TOTAL", border=1)
    pdf.cell(col_widths_main[2], 8, f"{total_required_weight:.2f}", border=1)
    pdf.cell(col_widths_main[3], 8, f"{total_used_weight:.2f}", border=1)
    pdf.cell(col_widths_main[4], 8, f"{total_waste_weight:.2f}", border=1)
    pdf.cell(col_widths_main[5], 8, "", border=1)  # Waste % total left blank
    pdf.cell(col_widths_main[6], 8, f"{total_cost:.2f}", border=1)
    pdf.ln(10)

    # ----------------------
    # Waste Report Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Detailed Waste Report (per group of bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_waste = [25, 35, 25, 35]
    headers_waste = ["Diameter", "Waste Length (m)", "Number of Bars", "Waste Weight (kg)"]

    for i, header in enumerate(headers_waste):
        pdf.cell(col_widths_waste[i], 8, header, border=1, align="C")
    pdf.ln()

    total_waste_weight2 = 0
    for _, row in waste_df.iterrows():
        pdf.cell(col_widths_waste[0], 8, f"{int(row['Diameter'])}mm", border=1)
        pdf.cell(col_widths_waste[1], 8, f"{row['Waste Length (m)']:.2f}", border=1)
        pdf.cell(col_widths_waste[2], 8, f"{int(row['Number of Bars'])}", border=1)
        pdf.cell(col_widths_waste[3], 8, f"{row['Waste Weight (kg)']:.2f}", border=1)
        pdf.ln()
        total_waste_weight2 += row['Waste Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_waste[0]+col_widths_waste[1]+col_widths_waste[2], 8, "TOTAL", border=1)
    pdf.cell(col_widths_waste[3], 8, f"{total_waste_weight2:.2f}", border=1)
    pdf.ln(10)

    # ----------------------
    # Purchase Summary Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Purchase Summary (12m Bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_purchase = [25, 35, 35]
    headers_purchase = ["Diameter", "Number of Bars", "Weight (kg)"]

    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()

    total_purchase_weight = 0
    for _, row in purchase_df.iterrows():
        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])}mm", border=1)
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1)
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1)
        pdf.ln()
        total_purchase_weight += row['Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_purchase[0]+col_widths_purchase[1], 8, "TOTAL", border=1)
    pdf.cell(col_widths_purchase[2], 8, f"{total_purchase_weight:.2f}", border=1)
    pdf.ln(10)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename

# =========================
# Streamlit App
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

if st.button("Reset"):
    st.session_state.clear()
    st.rerun()

price = st.number_input("Price per ton (optional)", min_value=0.0)
currency = "$"  # Fixed to Dollar

st.markdown("## Enter Rebar Data")
data = {}
purchase_summary_list = []

for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length": 0.0, "Quantity": 0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1, col2 = st.columns(2)
            rows[i]["Length"] = col1.number_input(
                f"Length (m) [{i+1}] - Ø{d}",
                value=float(rows[i]["Length"]),
                key=f"len_{d}_{i}"
            )
            rows[i]["Quantity"] = col2.number_input(
                f"Quantity [{i+1}] - Ø{d}",
                value=int(rows[i]["Quantity"]),
                min_value=0,
                key=f"qty_{d}_{i}"
            )
        if st.button(f"Add Row Ø{d}"):
            st.session_state[f"rows_{d}"].append({"Length": 0.0, "Quantity": 0})
            st.rerun()
        lengths_list = []
        for r in rows:
            lengths_list.extend([r["Length"]] * r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# =========================
# Run Optimization
# =========================
if st.button("Run Optimization"):
    results = []
    waste_dict = defaultdict(lambda: {"count":0, "weight":0})
    purchase_summary_list = []

    for d, lengths in data.items():
        solution, _ = optimize_cutting(lengths)
        total_required = sum(lengths)
        used_bars = len(solution)
        total_bar_length = used_bars * BAR_LENGTH
        wpm = weight_per_meter(d)
        required_weight = total_required * wpm
        used_weight = total_bar_length * wpm
        waste_weight = (total_bar_length - total_required) * wpm
        waste_percent = ((total_bar_length - total_required) / total_bar_length) * 100
        cost = (used_weight / 1000) * price if price else 0
        results.append([d, used_bars, required_weight, used_weight, waste_weight, waste_percent, cost])

        # Waste details
        for bar in solution:
            bar_total_length = sum(bar)
            bar_waste = BAR_LENGTH - bar_total_length
            if bar_waste > 0:
                key = (d, round(bar_waste, 6))
                waste_dict[key]["count"] += 1
                waste_dict[key]["weight"] += bar_waste * wpm

        # Purchase summary (full bars 12m)
        full_bars = sum(1 for bar in solution if sum(bar)==BAR_LENGTH)
        purchase_summary_list.append([d, full_bars, full_bars*BAR_LENGTH*wpm])

    df = pd.DataFrame(results, columns=["Diameter","Bars Used","Required Weight (kg)","Used Weight (kg)","Waste Weight (kg)","Waste %","Cost"])
    waste_data = []
    for (diameter, waste_length), info in waste_dict.items():
        waste_data.append([diameter, waste_length, info["count"], info["weight"]])
    waste_df = pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    purchase_df = pd.DataFrame(purchase_summary_list, columns=["Diameter","Bars","Weight (kg)"])

    st.success("Optimization Completed Successfully ✅")
    st.markdown("### Main Report")
    st.dataframe(df)
    st.markdown("### Detailed Waste Report")
    st.dataframe(waste_df)
    st.markdown("### Purchase Summary")
    st.dataframe(purchase_df)

    pdf_file = generate_pdf(df, waste_df, purchase_df, price)
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=pdf_file,
            mime="application/pdf"
        )
