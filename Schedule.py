import pandas as pd
from gurobipy import *

def setup_model(free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4):
    # Create Gurobi model
    m = Model("WorkSchedule")
    # Logging
    m.setParam('OutputFlag', 1)
    m.setParam('LogFile', 'schedule.log')

    # Decision variables
    schedule = {}
    off = {}
    for i in free_times.index:
        for day in days:
            for hour in part_times:
                schedule[i, day, hour] = m.addVar(
                    vtype=GRB.BINARY, name=f"Schedule_{i}_{day}_{hour}"
                )
            off[i, day] = m.addVar(vtype=GRB.BINARY, name=f"IsOff_{i}_{day}")

    # Staffing requirements for each shift
    for day in days:
        morning = quicksum(schedule[i, day, "morning"] for i in free_times.index)
        m.addConstr(morning == 3)

        noon = quicksum(schedule[i, day, "noon"] for i in free_times.index)
        afternoon = quicksum(schedule[i, day, "afternoon"] for i in free_times.index)
        m.addConstr(noon + afternoon == 9)

        evening = quicksum(schedule[i, day, "evening"] for i in free_times.index)
        m.addConstr(evening == 2)

    # Each employee works at most 2 shifts per day unless they take the day off
    for i in free_times.index:
        for day in days:
            total_hours = quicksum(schedule[i, day, ca] for ca in part_times)
            m.addConstr(total_hours <= 2 * (1 - off[i, day]))

    # No shift assigned when the employee is off
    for i in free_times.index:
        for day in days:
            for hour in part_times:
                m.addConstr(schedule[i, day, hour] + off[i, day] <= 1)

    # Respect employee availability
    for i in free_times.index:
        for day in days:
            for hour in part_times:
                m.addConstr(
                    schedule[i, day, hour] <= binary_free_times[i, day, hour] * (1 - off[i, day])
                )

    # Prevent two non-consecutive shifts in the same day
    for i in free_times.index:
        for day in days:
            m.addConstr(schedule[i, day, "noon"] + schedule[i, day, "afternoon"] <= 1 * (1 - off[i, day]))
            m.addConstr(schedule[i, day, "morning"] + schedule[i, day, "afternoon"] <= 1 * (1 - off[i, day]))
            m.addConstr(schedule[i, day, "morning"] + schedule[i, day, "evening"] <= 1 * (1 - off[i, day]))

    # Objective: minimize total weighted rank score
    total_hours_all = (
        quicksum(rank1[i] * schedule[i, day, "morning"]   for i in free_times.index for day in days)
        + quicksum(rank2[i] * schedule[i, day, "noon"]    for i in free_times.index for day in days)
        + 2 * quicksum(rank3[i] * schedule[i, day, "afternoon"] for i in free_times.index for day in days)
        + quicksum(rank4[i] * schedule[i, day, "evening"] for i in free_times.index for day in days)
    )
    m.setObjective(total_hours_all, GRB.MINIMIZE)

    # Solve
    m.optimize()
    return m, schedule, off

def generate_schedule_output(schedule, free_times, days):
    schedule_out = {"NAME": [], "MON": [], "TUE": [], "WED": [], "THU": [], "FRI": []}

    for i in free_times.index:
        schedule_out["NAME"].append(free_times["NAME"][i])
        for day in days:
            # Map binary schedule variables to readable time ranges
            if   schedule[i, day, "morning"].x > 0.5 and all(
                    schedule[i, day, s].x < 0.5 for s in ("noon", "afternoon", "evening")):
                schedule_out[day].append("6h-10h")

            elif schedule[i, day, "morning"].x > 0.5 and schedule[i, day, "noon"].x > 0.5:
                schedule_out[day].append("6h-13h" if free_times[f'{day}_OUT'][i] == 13 else "6h-14h")

            elif schedule[i, day, "noon"].x > 0.5 and all(
                    schedule[i, day, s].x < 0.5 for s in ("morning", "afternoon", "evening")):
                if   free_times[f'{day}_OUT'][i] == 13: schedule_out[day].append("9h-13h")
                elif free_times[f'{day}_OUT'][i] == 14: schedule_out[day].append("10h-14h")
                elif free_times[f'{day}_IN'][i]  == 11 or free_times[f'{day}_OUT'][i] == 15:
                    schedule_out[day].append("11h-15h")
                else: schedule_out[day].append("10h-14h")

            elif schedule[i, day, "noon"].x > 0.5 and schedule[i, day, "evening"].x > 0.5:
                schedule_out[day].append("11h-18h" if free_times[f'{day}_IN'][i] == 11 else "10h-18h")

            elif schedule[i, day, "afternoon"].x > 0.5 and all(
                    schedule[i, day, s].x < 0.5 for s in ("morning", "noon", "evening")):
                if   free_times[f'{day}_OUT'][i] == 13: schedule_out[day].append("12h-13h")
                elif free_times[f'{day}_OUT'][i] == 14: schedule_out[day].append("12h-14h")
                elif free_times[f'{day}_OUT'][i] == 15: schedule_out[day].append("12h-15h")
                else: schedule_out[day].append("12h-16h")

            elif schedule[i, day, "afternoon"].x > 0.5 and schedule[i, day, "evening"].x > 0.5:
                schedule_out[day].append("12h-18h")

            elif schedule[i, day, "evening"].x > 0.5 and all(
                    schedule[i, day, s].x < 0.5 for s in ("morning", "noon", "afternoon")):
                if   free_times[f'{day}_IN'][i] == 14: schedule_out[day].append("14h-18h")
                elif free_times[f'{day}_IN'][i] == 15: schedule_out[day].append("15h-18h")
                elif free_times[f'{day}_IN'][i] == 16: schedule_out[day].append("16h-18h")
                else: schedule_out[day].append("16h-18h")
            else:
                schedule_out[day].append("OFF")

    data = pd.DataFrame(schedule_out)
    print("\nEmployee work schedule:")
    print(data)
    data.to_excel('schedule_out.xlsx', index=True)
    return data

# ---------- Input data ----------
free_times = pd.read_excel('schedule_in.xlsx')

rank1 = free_times["RANK_MORNING"]
rank2 = free_times["RANK_NOON"]
rank3 = free_times["RANK_AFTERNOON"]
rank4 = free_times["RANK_EVENING"]

part_times = {"morning", "noon", "afternoon", "evening"}
days = ("MON", "TUE", "WED", "THU", "FRI")

# Convert availability to binary format
binary_free_times = {}
for i in free_times.index:
    for day in days:
        binary_free_times[i, day, "morning"]  = int(free_times[f'{day}_IN'][i] <= 6  and free_times[f'{day}_OUT'][i] >= 10)
        binary_free_times[i, day, "noon"]     = int(free_times[f'{day}_IN'][i] <= 11 and free_times[f'{day}_OUT'][i] >= 13)
        binary_free_times[i, day, "afternoon"]= int(free_times[f'{day}_IN'][i] <= 12 and free_times[f'{day}_OUT'][i] >= 13)
        binary_free_times[i, day, "evening"]  = int(free_times[f'{day}_IN'][i] <= 16 and free_times[f'{day}_OUT'][i] >= 18)

# Build and solve the model
m, schedule, off = setup_model(
    free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4
)

# If infeasible, add a full-time backup worker and retry
while m.status != GRB.OPTIMAL:
    print("\nNo feasible schedule found – adding backup worker...\n")
    backup = {
        "NAME": "AS",
        "MON_IN": 6, "MON_OUT": 18,
        "TUE_IN": 6, "TUE_OUT": 18,
        "WED_IN": 6, "WED_OUT": 18,
        "THU_IN": 6, "THU_OUT": 18,
        "FRI_IN": 6, "FRI_OUT": 18,
        "RANK_MORNING": 3,
        "RANK_NOON": 3,
        "RANK_AFTERNOON": 3,
        "RANK_EVENING": 3
    }
    free_times = pd.concat([free_times, pd.DataFrame([backup])], ignore_index=True)
    rank1 = free_times["RANK_MORNING"]
    rank2 = free_times["RANK_NOON"]
    rank3 = free_times["RANK_AFTERNOON"]
    rank4 = free_times["RANK_EVENING"]

    # Re-encode availability
    binary_free_times = {}
    for i in free_times.index:
        for day in days:
            binary_free_times[i, day, "morning"]  = int(free_times[f'{day}_IN'][i] <= 6  and free_times[f'{day}_OUT'][i] >= 10)
            binary_free_times[i, day, "noon"]     = int(free_times[f'{day}_IN'][i] <= 11 and free_times[f'{day}_OUT'][i] >= 13)
            binary_free_times[i, day, "afternoon"]= int(free_times[f'{day}_IN'][i] <= 12 and free_times[f'{day}_OUT'][i] >= 13)
            binary_free_times[i, day, "evening"]  = int(free_times[f'{day}_IN'][i] <= 16 and free_times[f'{day}_OUT'][i] >= 18)

    m, schedule, off = setup_model(
        free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4
    )

# Export schedule if model is optimal
if m.status == GRB.OPTIMAL:
    generate_schedule_output(schedule, free_times, days)
