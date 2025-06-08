import pandas as pd
from gurobipy import *

def setup_model(free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4):
    # Tạo mô hình
    m = Model("LichLamViec")
    # Ghi log 
    m.setParam('OutputFlag', 1)
    m.setParam('LogFile', 'schedule.log')
    # Tạo biến
    schedule = {}
    off = {}
    for i in free_times.index:
        for day in days:
            for hour in part_times:
                schedule[i, day, hour] = m.addVar(vtype=GRB.BINARY, name=f"Lich_{i}_{day}_{hour}")
            off[i, day] = m.addVar(vtype=GRB.BINARY, name=f"IsOff_{i}_{day}")

    # Thêm ràng buộc số lượng nhân viên trong mỗi ca
    for day in days:
        morning = quicksum(schedule[i, day, "morning"] for i in free_times.index)
        m.addConstr(morning == 3)

        noon = quicksum(schedule[i, day, "noon"] for i in free_times.index)
        afternoon = quicksum(schedule[i, day, "afternoon"] for i in free_times.index)
        m.addConstr(noon + afternoon == 9)

        evening = quicksum(schedule[i, day, "evening"] for i in free_times.index)
        m.addConstr(evening == 2)

    # Thêm ràng buộc thời gian làm việc của từng nhân viên
    for i in free_times.index:
        for day in days:
            total_hours = quicksum(schedule[i, day, ca] for ca in part_times)
            m.addConstr(total_hours <= 2 * (1 - off[i, day]))

    for i in free_times.index:
        for day in days:
            for hour in part_times:
                m.addConstr(schedule[i, day, hour] + off[i, day] <=1)
    for i in free_times.index:
        for day in days:
            for hour in part_times:
                m.addConstr(schedule[i, day, hour] <= binary_free_times[i, day, hour] * (1-off[i, day])) 

    # Thêm ràng buộc để không có nhân viên nào bị làm hai ca không sát nhau
    for i in free_times.index:
        for day in days:
            m.addConstr(schedule[i, day, "noon"] + schedule[i, day, "afternoon"] <= 1*(1-off[i, day]))
            m.addConstr(schedule[i, day, "morning"] + schedule[i, day, "afternoon"] <= 1*(1-off[i, day]))
            m.addConstr(schedule[i, day, "morning"] + schedule[i, day, "evening"] <= 1*(1-off[i, day]))

    # Thiết lập hàm mục tiêu
    total_hours_all = quicksum(rank1[i]*schedule[i, day, "morning"] for i in free_times.index for day in days) + quicksum(
        rank2[i]*schedule[i, day, "noon"] for i in free_times.index for day in days) + 2 * quicksum(
        rank3[i]*schedule[i, day, "afternoon"] for i in free_times.index for day in days) + quicksum(
        rank4[i]*schedule[i, day, "evening"] for i in free_times.index for day in days)

    m.setObjective(total_hours_all, GRB.MINIMIZE)

    # Gọi solver để giải bài toán
    m.optimize()

    return m, schedule, off

def generate_schedule_output(schedule, free_times, days):
    schedule_out = {"NAME": [], "MON": [], "TUE": [], "WED": [], "THU": [], "FRI": []}
    for i in free_times.index:
        schedule_out["NAME"].append(free_times["NAME"][i])
        for day in days:
            if schedule[i, day, "morning"].x > 0.5 and schedule[i, day, "noon"].x < 0.5 and schedule[i, day, "afternoon"].x < 0.5 and schedule[i, day, "evening"].x < 0.5:
                schedule_out[day].append("6h-10h")
            elif schedule[i, day, "morning"].x > 0.5 and schedule[i, day, "noon"].x > 0.5:   
                if free_times[f'{day}_OUT'][i] == 13 :
                    schedule_out[day].append("6h-13h")
                else: 
                    schedule_out[day].append("6h-14h")
            elif schedule[i, day, "morning"].x < 0.5 and schedule[i, day, "noon"].x > 0.5 and schedule[i, day, "afternoon"].x < 0.5 and schedule[i, day, "evening"].x < 0.5:
                if free_times[f'{day}_OUT'][i] == 13 :
                    schedule_out[day].append("9h-13h")
                elif free_times[f'{day}_OUT'][i] == 14:
                    schedule_out[day].append("10h-14")
                elif free_times[f'{day}_IN'][i] == 11 or free_times[f'{day}_OUT'][i] == 15 :
                    schedule_out[day].append("11h-15h")
                else: 
                    schedule_out[day].append("10h-14h")
            elif schedule[i, day, "morning"].x < 0.5 and schedule[i, day, "noon"].x > 0.5 and schedule[i, day, "afternoon"].x < 0.5 and schedule[i, day, "evening"].x > 0.5:
                if free_times[f'{day}_IN'][i] == 11:
                    schedule_out[day].append("11h-18h")
                else: 
                    schedule_out[day].append("10h-18h")
            elif schedule[i, day, "morning"].x < 0.5 and schedule[i, day, "noon"].x < 0.5 and schedule[i, day, "afternoon"].x > 0.5 and schedule[i, day, "evening"].x < 0.5:
                if free_times[f'{day}_OUT'][i] == 13:
                    schedule_out[day].append("12h-13h")
                elif free_times[f'{day}_OUT'][i] == 14:
                    schedule_out[day].append("12h-14h")
                elif free_times[f'{day}_OUT'][i] == 15:
                    schedule_out[day].append("12h-15h")
                else: 
                    schedule_out[day].append("12h-16h")
            elif schedule[i, day, "morning"].x < 0.5 and schedule[i, day, "noon"].x < 0.5 and schedule[i, day, "afternoon"].x > 0.5 and schedule[i, day, "evening"].x > 0.5:
                schedule_out[day].append("12h-18h")
            elif schedule[i, day, "morning"].x < 0.5 and schedule[i, day, "noon"].x < 0.5 and schedule[i, day, "afternoon"].x < 0.5 and schedule[i, day, "evening"].x > 0.5:
                if free_times[f'{day}_IN'][i] == 14:
                    schedule_out[day].append("14h-18h")
                elif free_times[f'{day}_IN'][i] == 15:
                    schedule_out[day].append("15h-18h")
                elif free_times[f'{day}_IN'][i] == 16:
                    schedule_out[day].append("16h-18h")
                else: 
                    schedule_out[day].append("16h-18h")
            else: schedule_out[day].append("OFF")
    data = pd.DataFrame(schedule_out)
    print("\nLịch làm việc của các nhân viên:")
    print(data)
    data.to_excel('schedule_out.xlsx', index=True)

    return data

# Các thông tin đầu vào

free_times = pd.read_excel('C:\\Users\\Administrator\\OneDrive\\Desktop\\schedule_in.xlsx') # Nhập file excel 

rank1 = free_times["RANK_MORNING"]
rank2 = free_times["RANK_NOON"]
rank3 = free_times["RANK_AFTERNOON"]
rank4 = free_times["RANK_EVENING"]
part_times = {
    "morning",
    "noon",
    "afternoon",
    "evening"
}
days = ("MON", "TUE", "WED", "THU", "FRI")

# Đưa thời gian rảnh thành dạng nhị phân
binary_free_times = {}
for i in free_times.index:
    for day in days:
        if free_times[f'{day}_IN'][i] <= 6 and free_times[f'{day}_OUT'][i] >= 10 : 
            binary_free_times[i, day, "morning"] = 1
        else: binary_free_times[i, day, "morning"] = 0
        if free_times[f'{day}_IN'][i] <= 11 and free_times[f'{day}_OUT'][i] >= 13:
            binary_free_times[i, day, "noon"] = 1
        else: binary_free_times[i, day, "noon"] = 0
        if free_times[f'{day}_IN'][i] <= 12 and free_times[f'{day}_OUT'][i] >= 13:
            binary_free_times[i, day, "afternoon"] = 1
        else: binary_free_times[i, day, "afternoon"] = 0
        if free_times[f'{day}_IN'][i] <= 16 and free_times[f'{day}_OUT'][i] >= 18:
            binary_free_times[i, day, "evening"] = 1
        else: binary_free_times[i, day, "evening"] = 0

m, schedule, off = setup_model(free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4)

while m.status != GRB.OPTIMAL:
    print("\nKhông có lịch tối ưu\n")
    need = {"NAME": "AS", 
            "MON_IN": 6, "MON_OUT":18, 
            "TUE_IN": 6, "TUE_OUT":18, 
            "WED_IN": 6, "WED_OUT":18, 
            "THU_IN": 6, "THU_OUT":18, 
            "FRI_IN": 6, "FRI_OUT":18,
            "RANK_MORNING": 3,
            "RANK_NOON": 3,
            "RANK_AFTERNOON": 3,
            "RANK_EVENING": 3}
    free_times = pd.concat([free_times, pd.DataFrame([need])], ignore_index= True)
    rank1 = free_times["RANK_MORNING"]
    rank2 = free_times["RANK_NOON"]
    rank3 = free_times["RANK_AFTERNOON"]
    rank4 = free_times["RANK_EVENING"]
    # Đưa thời gian rảnh thành dạng nhị phân
    binary_free_times = {}
    for i in free_times.index:
        for day in days:
            if free_times[f'{day}_IN'][i] <= 6 and free_times[f'{day}_OUT'][i] >= 10 : 
                binary_free_times[i, day, "morning"] = 1
            else: binary_free_times[i, day, "morning"] = 0
            if free_times[f'{day}_IN'][i] <= 11 and free_times[f'{day}_OUT'][i] >= 13:
                binary_free_times[i, day, "noon"] = 1
            else: binary_free_times[i, day, "noon"] = 0
            if free_times[f'{day}_IN'][i] <= 12 and free_times[f'{day}_OUT'][i] >= 13:
                binary_free_times[i, day, "afternoon"] = 1
            else: binary_free_times[i, day, "afternoon"] = 0
            if free_times[f'{day}_IN'][i] <= 16 and free_times[f'{day}_OUT'][i] >= 18:
                binary_free_times[i, day, "evening"] = 1
            else: binary_free_times[i, day, "evening"] = 0
    # Tạo mô hình và giải lại bài toán
    m, schedule, off = setup_model(free_times, part_times, days, binary_free_times, rank1, rank2, rank3, rank4)
# Xuất lịch
if m.status == GRB.OPTIMAL:
    generate_schedule_output(schedule, free_times, days)
        

