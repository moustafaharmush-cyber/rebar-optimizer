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
# Weight Formula
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

    return best_solution


# =========================
# PDF Generator
# =========================
def generate_pdf(df, purchase_df, price):

    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(10)

    # =========================
    # MAIN REPORT (NO COST)
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Main Report", ln=True)
    pdf.set_font("Arial", '', 9)

    col_widths_main = [30, 30, 40, 40, 40, 30]
    headers_main = ["Diameter", "Bars Used", "Required W (kg)",
                    "Used W (kg)", "Waste W (kg)", "Waste %"]

    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_required = 0
    total_used = 0
    total_waste = 0

    for _, row in df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_main[1], 8, f"{int(row['Bars Used'])}", border=1, align="C")
        pdf.cell(col_widths_main[2], 8, f"{row['Required Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[3], 8, f"{row['Used Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[4], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[5], 8, f"{row['Waste %']:.2f}", border=1, align="C")
        pdf.ln()

        total_required += row['Required Weight (kg)']
        total_used += row['Used Weight (kg)']
        total_waste += row['Waste Weight (kg)']

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(col_widths_main[0] + col_widths_main[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_main[2], 8, f"{total_required:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{total_used:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[4], 8, f"{total_waste:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[5], 8, "", border=1, align="C")
    pdf.ln(15)

    # =========================
    # PURCHASE SUMMARY (WITH COST)
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Purchase Summary (12m Bars)", ln=True)
    pdf.set_font("Arial", '', 9)

    col_widths_purchase = [40, 40, 50, 40]
    headers_purchase = ["Diameter", "Bars (12m)", "Weight (kg)", "Cost ($)"]

    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()

    total_weight = 0
    total_cost = 0

    for _, row in purchase_df.iterrows():
        cost = (row['Weight (kg)'] / 1000) * price

        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_purchase[3], 8, f"{cost:.2f}", border=1, align="C")
        pdf.ln()

        total_weight += row['Weight (kg)']
        total_cost += cost

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(col_widths_purchase[0] + col_widths_purchase[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_purchase[2], 8, f"{total_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_purchase[3], 8, f"{total_cost:.2f}", border=1, align="C")
    pdf.ln(15)

    # =========================
    # FINAL BIG TOTAL COST
    # =========================
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 12, f"TOTAL PURCHASE COST: {total_cost:.2f} $", border=1, align="C")

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename


# =========================
# STREAMLIT UI
# =========================

st.title("Rebar Optimizer Pro")

price = st.number_input("Price per ton ($)", value=1000.0)

results = []
purchase_data = []

for diameter in DIAMETERS:

    st.subheader(f"Diameter {diameter} mm")

    lengths = []
    for i in range(4):
        col1, col2 = st.columns(2)
        with col1:
            length = st.number_input(f"Length (m) [{i+1}] - {diameter} mm",
                                     min_value=0.0, step=0.5, key=f"l{diameter}{i}")
        with col2:
            qty = st.number_input(f"Quantity [{i+1}] - {diameter} mm",
                                  min_value=0, step=1, key=f"q{diameter}{i}")

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

    st.subheader("Main Report")
    st.dataframe(df)

    st.subheader("Purchase Summary (12m Bars)")
    st.dataframe(purchase_df)

    if st.button("Generate PDF Report"):
        file = generate_pdf(df, purchase_df, price)
        with open(file, "rb") as f:
            st.download_button("Download PDF", f, file_name=file)
