import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime

# =========================
# Settings
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 2000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

# =========================
# Weight Formula
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162


# =========================
# Cutting Optimization (Strong Version)
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

    return best_solution


# =========================
# PDF Generator
# =========================
def generate_pdf(df, purchase_df, price):

    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(10)

    # Main Report
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Main Report", ln=True)
    pdf.set_font("Arial", '', 9)

    col = [30, 30, 40, 40, 40, 30]
    headers = ["Diameter", "Bars Used", "Required W (kg)",
               "Used W (kg)", "Waste W (kg)", "Waste %"]

    for i, h in enumerate(headers):
        pdf.cell(col[i], 8, h, 1, 0, "C")
    pdf.ln()

    total_required = total_used = total_waste = 0

    for _, row in df.iterrows():
        pdf.cell(col[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")
        pdf.cell(col[1], 8, f"{int(row['Bars Used'])}", 1, 0, "C")
        pdf.cell(col[2], 8, f"{row['Required Weight (kg)']:.2f}", 1, 0, "C")
        pdf.cell(col[3], 8, f"{row['Used Weight (kg)']:.2f}", 1, 0, "C")
        pdf.cell(col[4], 8, f"{row['Waste Weight (kg)']:.2f}", 1, 0, "C")
        pdf.cell(col[5], 8, f"{row['Waste %']:.2f}", 1, 1, "C")

        total_required += row['Required Weight (kg)']
        total_used += row['Used Weight (kg)']
        total_waste += row['Waste Weight (kg)']

    pdf.ln(10)

    # Purchase Summary
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Purchase Summary (12m Bars)", ln=True)
    pdf.set_font("Arial", '', 9)

    col2 = [40, 40, 50, 40]
    headers2 = ["Diameter", "Bars (12m)", "Weight (kg)", "Cost ($)"]

    for i, h in enumerate(headers2):
        pdf.cell(col2[i], 8, h, 1, 0, "C")
    pdf.ln()

    total_cost = 0
    total_weight = 0

    for _, row in purchase_df.iterrows():
        cost = (row["Weight (kg)"] / 1000) * price
        total_cost += cost
        total_weight += row["Weight (kg)"]

        pdf.cell(col2[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")
        pdf.cell(col2[1], 8, f"{int(row['Bars'])}", 1, 0, "C")
        pdf.cell(col2[2], 8, f"{row['Weight (kg)']:.2f}", 1, 0, "C")
        pdf.cell(col2[3], 8, f"{cost:.2f}", 1, 1, "C")

    pdf.ln(15)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 12, f"TOTAL PURCHASE COST: {total_cost:.2f} $", 1, 1, "C")

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename


# =========================
# UI
# =========================

st.title("Rebar Optimizer Pro")

price = st.number_input("Price per ton ($)", value=1000.0)

input_data = {}

for diameter in DIAMETERS:

    st.subheader(f"Diameter {diameter} mm")

    if f"rows_{diameter}" not in st.session_state:
        st.session_state[f"rows_{diameter}"] = 1

    if st.button(f"Add Row - {diameter} mm"):
        st.session_state[f"rows_{diameter}"] += 1

    rows = st.session_state[f"rows_{diameter}"]
    diameter_data = []

    for i in range(rows):
        col1, col2 = st.columns(2)
        with col1:
            length = st.number_input(
                f"Length (m) - {diameter} mm - Row {i+1}",
                min_value=0.0,
                step=0.5,
                key=f"l{diameter}_{i}"
            )
        with col2:
            qty = st.number_input(
                f"Quantity - {diameter} mm - Row {i+1}",
                min_value=0,
                step=1,
                key=f"q{diameter}_{i}"
            )

        diameter_data.append((length, qty))

    input_data[diameter] = diameter_data


# ===== BUTTON TO RUN OPTIMIZATION =====
if st.button("Optimize Now"):

    results = []
    purchase_data = []

    for diameter in DIAMETERS:

        lengths = []
        for length, qty in input_data[diameter]:
            lengths += [length] * qty

        if lengths:
            bars = optimize_cutting(lengths)

            bars_used = len(bars)
            required_weight = sum(lengths) * weight_per_meter(diameter)
            used_weight = bars_used * BAR_LENGTH * weight_per_meter(diameter)
            waste_weight = used_weight - required_weight
            waste_percent = (waste_weight / used_weight) * 100 if used_weight else 0

            results.append({
                "Diameter": diameter,
                "Bars Used": bars_used,
                "Required Weight (kg)": required_weight,
                "Used Weight (kg)": used_weight,
                "Waste Weight (kg)": waste_weight,
                "Waste %": waste_percent
            })

            purchase_data.append({
                "Diameter": diameter,
                "Bars": bars_used,
                "Weight (kg)": used_weight
            })

    if results:
        df = pd.DataFrame(results)
        purchase_df = pd.DataFrame(purchase_data)

        st.success("Optimization Completed Successfully")
        st.dataframe(df)
        st.dataframe(purchase_df)

        file = generate_pdf(df, purchase_df, price)
        with open(file, "rb") as f:
            st.download_button("Download PDF", f, file_name=file)
