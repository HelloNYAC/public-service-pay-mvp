import pandas as pd

url = (
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/topics/pay/"
    "collective-agreements/ec.html"
)

tables = pd.read_html(url)

records = []

for level_num in range(1, 9):

    level = f"EC-{level_num:02d}"

    df = tables[level_num]

    latest = df.iloc[-1]
    
    print(latest["Effective Date"])

    for step in range(1, 6):

        salary = latest[f"Step {step}"]

        records.append(
            {
                "classification": "EC",
                "level": level,
                "step": step,
                "salary": int(salary)
            }
        )

for r in records[:20]:
    print(r)

print()
print("rows =", len(records))