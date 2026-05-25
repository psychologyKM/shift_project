
def add_consecutive_workdays_limit_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    consecutive_workdays_limit_personal_data シートを読み込み、
    各従業員の最大連続勤務日数を超えないようにする。

    想定するシート形式:
        name | maximum
        A | 5
        B | 4
        ...

    制約:
        maximum = 5 の場合、任意の6日間すべてに勤務することを禁止する。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "consecutive_workdays_limit_personal_data"
    )

    maximum_consecutive_workdays = {
        str(record["name"]).strip(): int(record["maximum"])
        for record in records
    }

    print()
    print("maximum_consecutive_workdays:")
    print(maximum_consecutive_workdays)

    for e in employees:
        if e not in maximum_consecutive_workdays:
            raise ValueError(
                f"consecutive_workdays_limit_personal_data に {e} がありません。"
            )

        max_consecutive = maximum_consecutive_workdays[e]

        if max_consecutive < 1:
            raise ValueError(
                f"{e} の maximum は1以上である必要があります: {max_consecutive}"
            )

        # 1日ごとの勤務有無を表す補助変数
        # work_on_day[(e, d)] = 1 なら、その日に何らかのjobに入っている
        work_on_day = {}

        for d in days:
            work_on_day[(e, d)] = model.NewBoolVar(
                f"work_on_day_{e}_{d}"
            )

            # すでに「1日1jobまで」の制約がある前提なので、
            # sum(x[(e, d, j)] for j in jobs) は 0 または 1 になる。
            model.Add(
                work_on_day[(e, d)] == sum(x[(e, d, j)] for j in jobs)
            )

        # max_consecutive + 1 日連続勤務を禁止
        window_size = max_consecutive + 1

        if window_size <= len(days):
            for start_idx in range(0, len(days) - window_size + 1):
                window_days = days[start_idx:start_idx + window_size]

                model.Add(
                    sum(work_on_day[(e, d)] for d in window_days)
                    <= max_consecutive
                )

    return maximum_consecutive_workdays
