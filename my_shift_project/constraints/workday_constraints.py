from modulators.modulate_with_special_care import (
    read_special_care_personal_data,
)


def add_exact_workdays_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
    max_diff=5,
    requested_off_days=None,
):
    """
    workdays_personal_data シートを読み込み、
    各従業員の「実質勤務日数」が指定値の±max_diff日以内になるように制約を追加する。

    ここでの実質勤務日数:
        実際にjobに入った日数 + 有給日数

    requested_off_days の形式:
        {
            (employee, date_str): "有給",
            (employee, date_str): "半休",
            ...
        }

    ただし、special_care_personal_data の ignore_workdays が 1 の従業員については、
    勤務日数制約・ズレ最小化の対象から除外する。
    """

    if requested_off_days is None:
        requested_off_days = {}

    workdays_records = read_worksheet_as_records(
        spreadsheet_url,
        "workdays_personal_data"
    )

    required_workdays = {
        str(record["name"]).strip(): int(record["workdays"])
        for record in workdays_records
    }

    ignore_workdays_employees = read_special_care_personal_data(
        spreadsheet_url,
        read_worksheet_as_records,
    )

    print()
    print("required_workdays:")
    print(required_workdays)

    print()
    print("ignore_workdays_employees:")
    print(ignore_workdays_employees)

    employee_workdays = {}
    employee_workdays_diff = {}

    for e in employees:
        employee_workdays[e] = model.NewIntVar(0, len(days), f"workdays_{e}")

        # 実際にjobに入った日数
        actual_assigned_workdays = sum(
            x[(e, d, j)]
            for d in days
            for j in jobs
        )

        # 有給日数は既知の定数として数える
        paid_leave_count = sum(
            1
            for d in days
            if requested_off_days.get((e, d)) == "有給"
        )

        # workdaysとして数える日数 = 出勤日 + 有給日
        model.Add(
            employee_workdays[e] == actual_assigned_workdays + paid_leave_count
        )

        if e in ignore_workdays_employees:
            print(f"勤務日数制約を除外: {e}")
            continue

        if e not in required_workdays:
            raise ValueError(
                f"workdays_personal_data に {e} の勤務日数がありません。"
            )

        employee_workdays_diff[e] = model.NewIntVar(
            0,
            len(days),
            f"workdays_diff_{e}"
        )

        model.AddAbsEquality(
            employee_workdays_diff[e],
            employee_workdays[e] - required_workdays[e]
        )

        # 指定勤務日数との差を±max_diff日以内にする
        model.Add(employee_workdays_diff[e] <= max_diff)

    return (
        employee_workdays,
        required_workdays,
        ignore_workdays_employees,
        employee_workdays_diff,
    )


# from modulators.modulate_with_special_care import (
#     read_special_care_personal_data,
# )


# def add_exact_workdays_constraints(
#     model,
#     x,
#     employees,
#     days,
#     jobs,
#     spreadsheet_url,
#     read_worksheet_as_records,
# ):
#     """
#     workdays_personal_data シートを読み込み、
#     各従業員の勤務日数が指定値と完全に一致するように制約を追加する。

#     ただし、special_care_personal_data の ignore_workdays が 1 の従業員については、
#     勤務日数制約を追加しない。
#     """

#     workdays_records = read_worksheet_as_records(
#         spreadsheet_url,
#         "workdays_personal_data"
#     )

#     required_workdays = {
#         record["name"]: int(record["workdays"])
#         for record in workdays_records
#     }

#     ignore_workdays_employees = read_special_care_personal_data(
#         spreadsheet_url,
#         read_worksheet_as_records,
#     )

#     print()
#     print("required_workdays:")
#     print(required_workdays)

#     print()
#     print("ignore_workdays_employees:")
#     print(ignore_workdays_employees)

#     employee_workdays = {}

#     for e in employees:
#         employee_workdays[e] = model.NewIntVar(0, len(days), f"workdays_{e}")

#         model.Add(
#             employee_workdays[e] == sum(x[(e, d, j)] for d in days for j in jobs)
#         )

#         if e in ignore_workdays_employees:
#             print(f"勤務日数制約を除外: {e}")
#             continue

#         if e not in required_workdays:
#             raise ValueError(
#                 f"workdays_personal_data に {e} の勤務日数がありません。"
#             )

#         model.Add(
#             employee_workdays[e] == required_workdays[e]
#         )

#     return employee_workdays, required_workdays, ignore_workdays_employees
