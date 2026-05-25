
def add_full_day_off_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    sunday_count,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    各従業員が、シフト期間中に
    法定休日数（=日曜日の数）+ 1日分以上の「全日休み」を取る制約を追加する。

    全日休みの定義:
      - その日にどのjobにも入っていない
      - かつ、前日に日付をまたぐ夜勤jobに入っていない

    list_job_across_midnight シートから、日付をまたぐjob一覧を読み込む。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "list_job_across_midnight"
    )

    # 1列だけのシートを想定
    # ヘッダー名が何であっても読めるように、各recordの最初の値を使う
    jobs_across_midnight = []

    for record in records:
        values = list(record.values())

        if len(values) == 0:
            continue

        job_name = str(values[0]).strip()

        if job_name != "":
            jobs_across_midnight.append(job_name)

    print()
    print("jobs_across_midnight:")
    print(jobs_across_midnight)

    # required_full_day_off_count = sunday_count + 1
    required_full_day_off_count = sunday_count

    full_day_off = {}

    for e in employees:
        for day_idx, d in enumerate(days):
            full_day_off[(e, d)] = model.NewBoolVar(
                f"full_day_off_{e}_{d}"
            )

            # その日の勤務数
            work_today = sum(x[(e, d, j)] for j in jobs)

            # 前日に日付をまたぐ夜勤に入っていたか
            if day_idx == 0:
                # 期間初日の前日はモデル外なので、ここでは「前日夜勤なし」と扱う
                across_midnight_previous_day = 0
            else:
                previous_day = days[day_idx - 1]
                across_midnight_previous_day = sum(
                    x[(e, previous_day, j)]
                    for j in jobs_across_midnight
                    if j in jobs
                )

            # full_day_off = 1 なら、その日は勤務なし
            model.Add(work_today == 0).OnlyEnforceIf(full_day_off[(e, d)])

            # full_day_off = 1 なら、前日に日付をまたぐ夜勤なし
            model.Add(across_midnight_previous_day == 0).OnlyEnforceIf(
                full_day_off[(e, d)]
            )

            # その日勤務なし、かつ前日夜勤なしなら full_day_off = 1
            model.Add(work_today + across_midnight_previous_day == 0).OnlyEnforceIf(
                full_day_off[(e, d)]
            )

            # full_day_off = 0 の場合は、勤務あり、または前日夜勤あり
            model.Add(work_today + across_midnight_previous_day >= 1).OnlyEnforceIf(
                full_day_off[(e, d)].Not()
            )

    # 各従業員が、法定休日数 + 1日以上の全日休みを取る
    for e in employees:
        model.Add(
            sum(full_day_off[(e, d)] for d in days) >= required_full_day_off_count
        )

    return full_day_off, jobs_across_midnight, required_full_day_off_count
