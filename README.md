# Employee Shift Scheduling Optimization with Gurobi

This project implements an optimal employee scheduling system using the **Gurobi Optimizer**. It generates a weekly work schedule (Monday to Friday) for staff based on their availability and evaluation scores for different time shifts.

---

## Features

- Reads employee availability and evaluation scores from an Excel file (`schedule_in.xlsx`)
- Converts availability into binary form for modeling
- Uses Gurobi to:
  - Allocate shifts fairly and efficiently
  - Enforce working constraints
  - Minimize total evaluation cost
- Automatically adds a backup worker if no feasible schedule exists
- Outputs results as a readable Excel file (`schedule_out.xlsx`)

---

## Input File Format – `schedule_in.xlsx`

Each row corresponds to one employee and must include:

- `NAME`: Employee name
- Daily availability:
  - `MON_IN`, `MON_OUT`, ..., `FRI_IN`, `FRI_OUT`: Working hours
- Evaluation scores (lower is better):
  - `RANK_MORNING`, `RANK_NOON`, `RANK_AFTERNOON`, `RANK_EVENING`

---

## ⏱ Time Shifts

| Shift       | Time        |
|-------------|-------------|
| morning     | 6h - 10h    |
| noon        | 10h - 13h   |
| afternoon   | 12h - 16h   |
| evening     | 16h - 18h   |

---

## Constraints

- 3 employees must work the **morning** shift each day
- 9 employees must cover **noon + afternoon** collectively
- 2 employees must work the **evening** shift each day
- Each employee can work **up to 2 shifts per day**
- Employees only work when available
- No employees are scheduled for non-consecutive shifts in a day (e.g., morning + evening)

---

## Objective Function

The goal is to **minimize the total evaluation cost** based on how suitable each employee is for a given shift.

<pre> total_cost = SUM( RANK_MORNING × morning_shifts + RANK_NOON × noon_shifts + 2 × RANK_AFTERNOON × afternoon_shifts + RANK_EVENING × evening_shifts ) </pre>
---

## Output

- A readable and formatted Excel file `schedule_out.xlsx` with each employee’s schedule in time ranges per day
- Example entries: `6h-10h`, `12h-18h`, `OFF`

---

## If No Feasible Schedule Found

If the initial setup fails:
- The script automatically adds a backup employee (`AS`) available full time
- Re-attempts to generate a valid schedule

---

## Requirements

- Python 3.x
- [Gurobi](https://www.gurobi.com) and Gurobi Python API
- `pandas` library


```bash
# 1. Install packages
pip install pandas
pip install gurobipy

# 2. Run the optimisation
python Schedule.py   

# 3. Results
# schedule_out.xlsx
```
