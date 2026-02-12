import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict

# =========================
# Basic Settings
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

# =========================
# Weight per meter formula
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# Cutting Optimization Algorithm
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
    return best_solution, min_waste

# =========================
# PDF Report Generator
# =========================
def generate_pdf(df, waste_df, full_bars_dict, price=None, currency="$"):
    pdf = FPDF(orientation='L')
    pdf.add_page()

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    if price:
        pdf.cell(0, 8, f"Price per Ton: {round(price,2)} {currency}", ln=True)
    pdf.ln(5)

    # -------------------------
    # Main Report Table
    # -------------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Main Report (Bars Used)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_main = [25, 25, 35, 35, 35, 25, 30]
    headers_main = ["Diameter", "Bars Used", "Required W (kg)", "Used W (kg)",
                    "Waste W (kg)", "Waste %", "Cost"]
    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_used_weight = 0
    total_waste_weight = 0
    total_cost = 0
    total_waste_percent_weighted = 0

    for _, row in df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])} mm", border=1)
        pdf.cell(col_widths_main[1], 8, f"{int(row['Bars Used'])}", border=1)
        pdf.cell(col_widths_main[2], 8, f"{round(row['Required Weight (kg)'],2)}", border=1)
        pdf.cell(col_widths_main[3], 8, f"{round(row['Used Weight (kg)'],2)}", border=1)
        pdf.cell(col_widths_main[4], 8, f"{round(row['Waste Weight (kg)'],2)}", border=1)
        pdf.cell(col_widths_main[5], 8, f"{round(row['Waste %'],2)}", border=1)
        pdf.cell(col_widths_main[6], 8, f"{round(row['Cost'],2)} {currency}", border=1)
        pdf.ln()

        # Accumulate totals
        total_used_weight += row['Used Weight (kg)']
        total_waste_weight += row['Waste Weight (kg)']
        total_cost += row['Cost']
        total_waste_percent_weighted += row['Waste %'] * row['Used Weight (kg)']

    # Calculate weighted average Waste %
    weighted_waste_percent = total_waste_percent_weighted / total_used_weight if total_used_weight else 0

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(sum(col_widths_main[:-2]), 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{round(total_used_weight,2)}", border=1, align="C")
    pdf.cell(col_widths_main[4], 8, f"{round(total_waste_weight,2)}", border=1, align="C")
    pdf.cell(col_widths_main[5], 8, f"{round(weighted_waste_percent,2)}", border=1, align="C")
    pdf.cell(col_widths_main[6], 8, f"{round(total_cost,2)} {currency}", border=1, align="C")
    pdf.ln(10)

    # -------------------------
    # Waste Report Table
    # -------------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Detailed Waste Report (per group of bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_waste = [25, 35, 25, 35]
    headers_waste = ["Diameter", "Waste Length (m)", "Number of Bars", "Waste Weight (kg)"]
    for i, header in enumerate(headers_waste):
        pdf.cell(col_widths_waste[i], 8, header, border=1, align="C")
    pdf.ln()

    total_waste_weight = 0
    total_waste_cost = 0
    for _, row in waste_df.iterrows():
        pdf.cell(col_widths_waste[0], 8, f"{int(row['Diameter'])} mm", border=1)
        pdf.cell(col_widths_waste[1], 8, f"{round(row['Waste Length (m)'],2)}", border=1)
        pdf.cell(col_widths_waste[2], 8, f"{int(row['Number of Bars'])}", border=1)
        pdf.cell(col_widths_waste[3], 8, f"{round(row['Waste Weight (kg)'],2)}", border=1)
        pdf.ln()
        total_waste_weight += row['Waste Weight (kg)']
        total_waste_cost += (row['Waste Weight (kg)']/1000)*price if price else 0

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(sum(col_widths_waste[:-1]), 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_waste[-1], 8, f"{round(total_waste_weight,2)}", border=1, align="C")
    pdf.cell(col_widths_waste[-1], 8, f"{round(total_waste_cost,2)} {currency}", border=1, align="C")
    pdf.ln(10)

    # -------------------------
    # Purchase Summary Table (Full 12m Bars)
    # -------------------------
    if full_bars_dict:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "Purchase Summary - Full 12m Bars", ln=True)
        pdf.set_font("Arial", '', 8)
        col_widths_full = [40, 40, 40]
        headers_full = ["Diameter", "Number of 12m Bars", "Weight (kg)"]
        for i, header in enumerate(headers_full):
            pdf.cell(col_widths_full[i], 8, header, border=1, align="C")
        pdf.ln()

        total_weight = 0
        for diameter, info in full_bars_dict.items():
            pdf.cell(col_widths_full[0], 8, f"{int(diameter)} mm", border=1)
            pdf.cell(col_widths_full[1], 8, str(info["count"]), border=1, align="C")
            pdf.cell(col_widths_full[2], 8, f"{round(info['weight'],2)}", border=1, align="C")
            pdf.ln()
            total_weight += info['weight']

        pdf.set_font("Arial", 'B', 8)
        pdf.cell(col_widths_full[0] + col_widths_full[1], 8, "TOTAL", border=1, align="C")
        pdf.cell(col_widths_full[2], 8, f"{round(total_weight,2)}", border=1, align="C")
        pdf.ln(10)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)
    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename
