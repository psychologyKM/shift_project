
def add_requested_off_day_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    date_info,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    requested_off_day_personal_data シートを読み込み、
    希望された休みの日は、全jobに入らないようにする。

    さらに type == "有給" の場合は、
    その前日に日付をまたぐ夜勤jobにも入らないようにする。

    想定するシート形式:
        name | month | day | type
        A | 6 | 8 | 有給
        A | 5 | 19 | 半休
        ...

    list_job_across_midnight シート:
        日付をまたぐjob名の一覧
    """

    # 希望休データを読み込む
    requested_off_records = read_worksheet_as_records(
        spreadsheet_url,
        "requested_off_day_personal_data"
    )

    # 日付をまたぐjob一覧を読み込む
    across_midnight_records = read_worksheet_as_records(
        spreadsheet_url,
        "list_job_across_midnight"
    )

    jobs_across_midnight = []

    for record in across_midnight_records:
        values = list(record.values())

        if len(values) == 0:
            continue

        job_name = str(values[0]).strip()

        if job_name != "":
            jobs_across_midnight.append(job_name)

    print()
    print("jobs_across_midnight for requested off:")
    print(jobs_across_midnight)

    requested_off_days = {}

    for record in requested_off_records:
        name = str(record["name"]).strip()
        month = int(record["month"])
        day = int(record["day"])
        off_type = str(record.get("type", "")).strip()

        matched_date_str = None

        for d in days:
            date_obj = date_info[d]["date"]

            if date_obj.month == month and date_obj.day == day:
                matched_date_str = d
                break

        # シフト期間外の日付は無視する
        if matched_date_str is None:
            continue

        requested_off_days[(name, matched_date_str)] = off_type

    print()
    print("requested_off_days:")
    for (name, d), off_type in requested_off_days.items():
        print(f"  {name}: {d} ({off_type})")

    # 希望休の日は、その人を全jobに割り当てない
    for (name, d), off_type in requested_off_days.items():
        if name not in employees:
            raise ValueError(
                f"requested_off_day_personal_data にある {name} が employees に存在しません。"
            )

        model.Add(
            sum(x[(name, d, j)] for j in jobs) == 0
        )

    # 有給の日は「fullの休日」として扱う
    # つまり、その前日に日付をまたぐ夜勤jobに入っていてはいけない
    for (name, d), off_type in requested_off_days.items():
        if off_type != "有給":
            continue

        day_idx = days.index(d)

        # 対象期間の初日の場合、前日はモデル外なのでここでは制約を追加しない
        if day_idx == 0:
            continue

        previous_day = days[day_idx - 1]

        model.Add(
            sum(
                x[(name, previous_day, j)]
                for j in jobs_across_midnight
                if j in jobs
            ) == 0
        )

    return requested_off_days
