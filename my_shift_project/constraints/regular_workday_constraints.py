
def add_regular_workday_constraints(
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
    regular_workday_personal_data シートを読み込み、
    指定された曜日には必ず勤務する制約を追加する。

    想定するシート形式:
        name | 月 | 火 | 水 | 木 | 金 | 土 | 日
        Aさん | 0 | 1 | 0 | 0 | 0 | 0 | 0

    1 が入っている曜日について、その従業員はその曜日の全日付で必ず何らかのjobに入る。
    """

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    records = read_worksheet_as_records(
        spreadsheet_url,
        "regular_workday_personal_data"
    )

    regular_workday_personal_data = {}

    for record in records:
        name = str(record["name"]).strip()
        regular_workday_personal_data[name] = {}

        for w in weekdays:
            regular_workday_personal_data[name][w] = int(record.get(w, 0))

    print()
    print("regular_workday_personal_data:")
    print(regular_workday_personal_data)

    for e in employees:
        if e not in regular_workday_personal_data:
            raise ValueError(
                f"regular_workday_personal_data に {e} がありません。"
            )

        for d in days:
            weekday = date_info[d]["weekday"]

            if regular_workday_personal_data[e][weekday] == 1:
                model.Add(
                    sum(x[(e, d, j)] for j in jobs) >= 1
                )

    return regular_workday_personal_data
