
def add_if_then_pair_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    if_then_pair シートを読み込み、
    employee_if が job_if を持っていた場合、
    employee_then を job_then に割り当てる制約を追加する。

    想定するシート形式:
        employee_if | job_if | employee_then | job_then
        a | 夕短 | b | 休

    job_then == "休" の場合:
        employee_then はその日にどのjobにも入らない。
        出力時には、requested_off_days にない非勤務日なので「公休」扱いになる。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "if_then_pair"
    )

    if_then_pairs = []

    print()
    print("if_then_pair:")

    for record in records:
        employee_if = str(record["employee_if"]).strip()
        job_if = str(record["job_if"]).strip()
        employee_then = str(record["employee_then"]).strip()
        job_then = str(record["job_then"]).strip()

        if employee_if not in employees:
            raise ValueError(
                f"if_then_pair の employee_if '{employee_if}' が employees に存在しません。"
            )

        if employee_then not in employees:
            raise ValueError(
                f"if_then_pair の employee_then '{employee_then}' が employees に存在しません。"
            )

        if job_if != "休" and job_if not in jobs:
            raise ValueError(
                f"if_then_pair の job_if '{job_if}' が jobs に存在しません。"
            )

        if job_then != "休" and job_then not in jobs:
            raise ValueError(
                f"if_then_pair の job_then '{job_then}' が jobs に存在しません。"
            )

        if_then_pairs.append({
            "employee_if": employee_if,
            "job_if": job_if,
            "employee_then": employee_then,
            "job_then": job_then,
        })

        print(
            f"  if {employee_if} = {job_if}, "
            f"then {employee_then} = {job_then}"
        )

    for pair_idx, pair in enumerate(if_then_pairs):
        employee_if = pair["employee_if"]
        job_if = pair["job_if"]
        employee_then = pair["employee_then"]
        job_then = pair["job_then"]

        for d in days:
            # 条件側: employee_if が job_if に入っているか
            if job_if == "休":
                trigger = model.NewBoolVar(
                    f"if_then_trigger_{pair_idx}_{employee_if}_{d}_rest"
                )

                work_if = sum(
                    x[(employee_if, d, j)]
                    for j in jobs
                )

                model.Add(work_if == 0).OnlyEnforceIf(trigger)
                model.Add(work_if >= 1).OnlyEnforceIf(trigger.Not())

            else:
                trigger = x[(employee_if, d, job_if)]

            # 帰結側: employee_then を job_then にする
            if job_then == "休":
                model.Add(
                    sum(x[(employee_then, d, j)] for j in jobs) == 0
                ).OnlyEnforceIf(trigger)

            else:
                model.Add(
                    x[(employee_then, d, job_then)] == 1
                ).OnlyEnforceIf(trigger)

    return if_then_pairs
