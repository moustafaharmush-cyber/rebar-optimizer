import streamlit as st
import random
import pandas as pd

# إعدادات أساسية
BAR_LENGTH = 12.0
ITERATIONS = 3000
diameters = [10,12,14,16,18,20,22,25]

# حساب وزن المتر الطولي لكل قطر
def weight_per_meter(d):
    return (d**2)/162

# خوارزمية تحسين قص القضبان
def optimize_cutting(lengths):
    best_solution = None
    min_waste = float('inf')
    min_bars = float('inf')

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

# إعداد صفحة Streamlit
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Mustafa Harmoush")

# إدخال سعر الطن (اختياري)
price = st.number_input("Price per ton (optional)", min_value=0.0)

# إدخال بيانات الأطوال والكميات لكل قطر
data = {}
st.markdown("## Enter Rebar Data")

for d in diameters:
    with st.expander(f"Diameter {d} mm"):
        lengths_input = st.text_area(
            f"Enter lengths and quantities (format: length,quantity)",
            key=f"text_{d}",
            placeholder="Example:\n3.5,10\n2.8,15"
        )
        if lengths_input:
            lines = lengths_input.split("\n")
            lengths = []
            for line in lines:
                if "," in line:
                    l, q = line.split(",")
                    lengths.extend([float(l)] * int(q))
            if lengths:
                data[d] = lengths

# تشغيل الحساب عند الضغط على الزر
if st.button("Run Optimization"):

    results = []

    for d, lengths in data.items():

        solution, waste = optimize_cutting(lengths)

        total_required = sum(lengths)
        used_bars = len(solution)
        total_bar_length = used_bars * BAR_LENGTH

        wpm = weight_per_meter(d)

        required_weight = total_required * wpm
        used_weight = total_bar_length * wpm
        waste_weight = waste * wpm
        waste_percent = (waste / total_bar_length)*100

        cost = (used_weight/1000)*price if price else 0

        results.append([
            d,
            used_bars,
            round(required_weight,2),
            round(used_weight,2),
            round(waste_weight,2),
            round(waste_percent,2),
            round(cost,2)
        ])

    df = pd.DataFrame(results, columns=[
        "Diameter",
        "Bars Used",
        "Required Weight (kg)",
        "Used Weight (kg)",
        "Waste Weight (kg)",
        "Waste %",
        "Cost"
    ])

    st.success("Optimization Completed ✅")
    st.dataframe(df)
