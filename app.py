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
# PDF GENERATOR
# =========================
def generate_pdf(df, waste_df, purchase_df, price):
    pdf=FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,"Rebar Optimization Report",ln=True,align="C")
    pdf.ln(5)
    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,"Created by Civil Engineer Moustafa Harmouch",ln=True)
    pdf.cell(0,8,f"Date: {datetime.date.today()}",ln=True)
    pdf.ln(5)

    # =========================
    # MAIN REPORT
    # =========================
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,"Main Report",ln=True)
    pdf.set_font("Arial",'',8)

    col_widths_main=[25,25,35,35,25,30]
    headers_main=["Diameter","Bars Used","Used W (kg)","Required W (kg)","Waste W (kg)","Waste %"]
    for i,h in enumerate(headers_main):
        pdf.cell(col_widths_main[i],8,h,border=1,align="C")
    pdf.ln()

    total_used=0
    total_required=0
    total_waste=0
    for _,row in df.iterrows():
        pdf.cell(col_widths_main[0],8,f"{int(row['Diameter'])} mm",border=1,align="C")
        pdf.cell(col_widths_main[1],8,f"{int(row['Bars Used'])}",border=1,align="C")
        pdf.cell(col_widths_main[2],8,f"{row['Used Weight (kg)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_main[3],8,f"{row['Required Weight (kg)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_main[4],8,f"{row['Waste Weight (kg)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_main[5],8,f"{row['Waste %']:.2f}",border=1,align="C")
        pdf.ln()
        total_used+=row['Used Weight (kg)']
        total_required+=row['Required Weight (kg)']
        total_waste+=row['Waste Weight (kg)']

    pdf.set_font("Arial",'B',8)
    pdf.cell(col_widths_main[0]+col_widths_main[1],8,"TOTAL",border=1,align="C")
    pdf.cell(col_widths_main[2],8,f"{total_used:.2f}",border=1,align="C")
    pdf.cell(col_widths_main[3],8,f"{total_required:.2f}",border=1,align="C")
    pdf.cell(col_widths_main[4],8,f"{total_waste:.2f}",border=1,align="C")
    pdf.cell(col_widths_main[5],8,"",border=1,align="C")
    pdf.ln(10)

    # =========================
    # WASTE REPORT
    # =========================
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,"Detailed Waste Report",ln=True)
    pdf.set_font("Arial",'',8)

    col_widths_waste=[25,35,25,35,30]
    headers_waste=["Diameter","Waste Length (m)","Number of Bars","Waste W (kg)","Cost ($)"]
    for i,h in enumerate(headers_waste):
        pdf.cell(col_widths_waste[i],8,h,border=1,align="C")
    pdf.ln()

    total_waste_cost=0
    for _,row in waste_df.iterrows():
        cost=row['Waste Weight (kg)']*price/1000
        pdf.cell(col_widths_waste[0],8,f"{int(row['Diameter'])} mm",border=1,align="C")
        pdf.cell(col_widths_waste[1],8,f"{row['Waste Length (m)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_waste[2],8,f"{int(row['Number of Bars'])}",border=1,align="C")
        pdf.cell(col_widths_waste[3],8,f"{row['Waste Weight (kg)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_waste[4],8,f"{cost:.2f}",border=1,align="C")
        pdf.ln()
        total_waste_cost+=cost

    pdf.set_font("Arial",'B',8)
    pdf.cell(col_widths_waste[0]+col_widths_waste[1]+col_widths_waste[2]+col_widths_waste[3],8,"TOTAL",border=1,align="C")
    pdf.cell(col_widths_waste[4],8,f"{total_waste_cost:.2f}",border=1,align="C")
    pdf.ln(10)

    # =========================
    # PURCHASE SUMMARY
    # =========================
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,"Purchase Summary (12m Bars)",ln=True)
    pdf.set_font("Arial",'',8)

    col_widths_purchase=[25,35,35,30]
    headers_purchase=["Diameter","Number of Bars","Weight (kg)","Cost ($)"]
    for i,h in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i],8,h,border=1,align="C")
    pdf.ln()

    total_purchase_cost=0
    total_purchase_weight=0
    for _,row in purchase_df.iterrows():
        cost=row['Weight (kg)']*price/1000
        pdf.cell(col_widths_purchase[0],8,f"{int(row['Diameter'])} mm",border=1,align="C")
        pdf.cell(col_widths_purchase[1],8,f"{int(row['Bars'])}",border=1,align="C")
        pdf.cell(col_widths_purchase[2],8,f"{row['Weight (kg)']:.2f}",border=1,align="C")
        pdf.cell(col_widths_purchase[3],8,f"{cost:.2f}",border=1,align="C")
        pdf.ln()
        total_purchase_cost+=cost
        total_purchase_weight+=row['Weight (kg)']

    pdf.set_font("Arial",'B',8)
    pdf.cell(col_widths_purchase[0]+col_widths_purchase[1],8,"TOTAL",border=1,align="C")
    pdf.cell(col_widths_purchase[2],8,f"{total_purchase_weight:.2f}",border=1,align="C")
    pdf.cell(col_widths_purchase[3],8,f"{total_purchase_cost:.2f}",border=1,align="C")
    pdf.ln(10)

    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,"Signature: ____________________",ln=True)

    filename=f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename
