
def add_weekly_dayoff_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    date_info,
    spreadsheet_url,
    read_worksheet_as_records,
    max_dayoff_weekdays=2,
):
    """
    各従業員について、公休曜日を探索させる。

    z[(e, w)] = 1 なら、従業員 e の公休曜日が w であることを表す。

    regular_holiday_personal_data シートで 1 が指定されている曜日は、
    必ず公休曜日として選ばれる。
    """

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    # regular_holiday_personal_data を読み込む
    regular_holiday_records = read_worksheet_as_records(
        spreadsheet_url,
        "regular_holiday_personal_data"
    )

    # {name: {weekday: 0/1}} の形に変換
    regular_holiday_personal_data = {}

    for record in regular_holiday_records:
        e = record["name"]
        regular_holiday_personal_data[e] = {}

        for w in weekdays:
            regular_holiday_personal_data[e][w] = int(record[w])

    print()
    print("regular_holiday_personal_data:")
    print(regular_holiday_personal_data)

    # デバッグ1: 希望公休が上限を超えていないか確認
    print()
    print("Requested regular holidays by employee")

    for e in employees:
        if e not in regular_holiday_personal_data:
            raise ValueError(
                f"regular_holiday_personal_data に {e} がありません。"
            )

        requested_weekdays = [
            w for w in weekdays
            if regular_holiday_personal_data[e][w] == 1
        ]

        print(f"  {e}: {requested_weekdays}")

        if len(requested_weekdays) > max_dayoff_weekdays:
            raise ValueError(
                f"{e} の希望公休が {len(requested_weekdays)} 個あります: "
                f"{requested_weekdays}。上限は {max_dayoff_weekdays} 個です。"
            )

    # デバッグ2: 希望公休によって休みになる日付を表示
    print()
    print("Requested regular holiday dates by employee")

    for e in employees:
        requested_weekdays = [
            w for w in weekdays
            if regular_holiday_personal_data[e][w] == 1
        ]

        requested_dates = [
            d for d in days
            if date_info[d]["weekday"] in requested_weekdays
        ]

        print(
            f"  {e}: {len(requested_dates)}日 - "
            f"{requested_weekdays} - {requested_dates}"
        )

    # z[(e, w)] = 1 なら、従業員 e の公休曜日が w
    z = {}

    for e in employees:
        for w in weekdays:
            z[(e, w)] = model.NewBoolVar(f"weekly_dayoff_{e}_{w}")

    # 希望公休がある曜日は、必ず公休にする
    for e in employees:
        for w in weekdays:
            if regular_holiday_personal_data[e][w] == 1:
                model.Add(z[(e, w)] == 1)

    # 各従業員は、公休曜日を最大 max_dayoff_weekdays 個持つ
    for e in employees:
        model.Add(
            sum(z[(e, w)] for w in weekdays) <= max_dayoff_weekdays
        )

    # z[(e, w)] = 1 なら、その曜日に該当する日はすべて勤務なし
    for e in employees:
        for d in days:
            weekday = date_info[d]["weekday"]

            model.Add(
                sum(x[(e, d, j)] for j in jobs) == 0
            ).OnlyEnforceIf(z[(e, weekday)])

    return z, weekdays, regular_holiday_personal_data
