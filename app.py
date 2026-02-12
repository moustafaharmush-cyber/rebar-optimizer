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
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_main[1], 8, f"{int(row['Bars Used'])}", border=1, align="C")
        pdf.cell(col_widths_main[2], 8, f"{row['Required Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[3], 8, f"{row['Used Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[4], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[5], 8, f"{row['Waste %']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[6], 8, f"{row['Cost']:.2f}", border=1, align="C")
        pdf.ln()
        total_required_weight += row['Required Weight (kg)']
        total_used_weight += row['Used Weight (kg)']
        total_waste_weight += row['Waste Weight (kg)']
        total_cost += row['Cost']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_main[0]+col_widths_main[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_main[2], 8, f"{total_required_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{total_used_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[4], 8, f"{total_waste_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_main[5], 8, "", border=1, align="C")
    pdf.cell(col_widths_main[6], 8, f"{total_cost:.2f}", border=1, align="C")
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
        pdf.cell(col_widths_waste[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_waste[1], 8, f"{row['Waste Length (m)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_waste[2], 8, f"{int(row['Number of Bars'])}", border=1, align="C")
        pdf.cell(col_widths_waste[3], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
        total_waste_weight2 += row['Waste Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_waste[0]+col_widths_waste[1]+col_widths_waste[2], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_waste[3], 8, f"{total_waste_weight2:.2f}", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Purchase Summary Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Purchase Summary (for 12m Bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_purchase = [25, 35, 35]
    headers_purchase = ["Diameter", "Number of Bars", "Weight (kg)"]

    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()

    total_purchase_weight = 0
    for _, row in purchase_df.iterrows():
        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
        total_purchase_weight += row['Weight (kg)']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_purchase[0]+col_widths_purchase[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_purchase[2], 8, f"{total_purchase_weight:.2f}", border=1, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename
