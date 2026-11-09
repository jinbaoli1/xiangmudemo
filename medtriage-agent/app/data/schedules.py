"""排班模拟数据生成器."""
import random
from datetime import datetime, timedelta


def generate_schedules(doctors, departments, num_days=14):
    """生成排班数据，未来14天的排班."""
    schedules = []
    schedule_id = 1
    random.seed(42)

    time_slots = [
        {"slot": "上午", "start": "08:00", "end": "12:00"},
        {"slot": "下午", "start": "14:00", "end": "17:30"},
    ]

    today = datetime.now().date()

    for day_offset in range(num_days):
        current_date = today + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        is_weekend = current_date.weekday() >= 5

        for dept_idx, dept in enumerate(departments):
            dept_id = dept_idx + 1
            # 获取该科室的医生
            dept_doctors = [d for d in doctors if d["department_id"] == dept_id]
            if not dept_doctors:
                continue

            for slot_info in time_slots:
                slot = slot_info["slot"]
                # 周末排班医生少一些
                if is_weekend:
                    num_on_duty = max(1, len(dept_doctors) // 2)
                else:
                    num_on_duty = max(1, len(dept_doctors) - 1)

                # 随机选择值班医生
                on_duty_doctors = random.sample(dept_doctors, min(num_on_duty, len(dept_doctors)))

                for doctor in on_duty_doctors:
                    # 根据职称和经验设置号源数
                    title = doctor["title"]
                    if "主任" in title:
                        total_quota = random.randint(15, 25)
                        fee = random.choice([100.0, 150.0, 200.0, 300.0])
                    elif "副主任" in title:
                        total_quota = random.randint(20, 30)
                        fee = random.choice([60.0, 80.0, 100.0])
                    elif "主治" in title:
                        total_quota = random.randint(25, 40)
                        fee = random.choice([30.0, 50.0, 60.0])
                    else:
                        total_quota = random.randint(30, 50)
                        fee = random.choice([20.0, 30.0])

                    # 剩余号源，模拟已预约一部分
                    remaining_quota = max(0, total_quota - random.randint(0, total_quota // 2))

                    schedules.append({
                        "id": schedule_id,
                        "doctor_id": doctor["id"],
                        "department_id": dept_id,
                        "date": date_str,
                        "time_slot": slot,
                        "total_quota": total_quota,
                        "remaining_quota": remaining_quota,
                        "fee": fee,
                    })
                    schedule_id += 1

    return schedules
