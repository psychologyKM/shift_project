
def add_necessary_consecutive_holidays_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    special_care_personal_data シートの necessary_consecutive_holidays_length を読み込み、
    各従業員について、指定された日数以上の連続休日を月に1回以上確保する。

    想定するシート形式:
        name | ... | necessary_consecutive_holidays_length
        Aさん | ... | 0
        Bさん | ... | 2

    意味:
        necessary_consecutive_holidays_length = 2 の人は、
        対象期間中に少なくとも1回、2日連続で勤務なしの日が必要。

    ここでの「休日」は、
        その日にどの job にも入っていない日
    として扱う。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "special_care_personal_data"
    )

    necessary_consecutive_holidays_length = {}

    for record in records:
        name = str(record["name"]).strip()

        length_raw = record.get("necessary_consecutive_holidays_length", 0)

        if length_raw == "":
            length = 0
        else:
            length = int(length_raw)

        necessary_consecutive_holidays_length[name] = length

    print()
    print("necessary_consecutive_holidays_length:")
    print(necessary_consecutive_holidays_length)

    consecutive_holiday_window_vars = {}

    for e in employees:
        length = necessary_consecutive_holidays_length.get(e, 0)

        # 0の場合は制約なし
        if length <= 0:
            continue

        if length > len(days):
            raise ValueError(
                f"{e} の necessary_consecutive_holidays_length={length} が "
                f"対象期間の日数 {len(days)} を超えています。"
            )

        window_vars = []

        for start_idx in range(0, len(days) - length + 1):
            window_days = days[start_idx:start_idx + length]

            window_var = model.NewBoolVar(
                f"consecutive_holidays_{e}_{start_idx}_{length}"
            )

            consecutive_holiday_window_vars[(e, start_idx)] = window_var
            window_vars.append(window_var)

            # window_var = 1 なら、その window_days はすべて勤務なし
            for d in window_days:
                model.Add(
                    sum(x[(e, d, j)] for j in jobs) == 0
                ).OnlyEnforceIf(window_var)

        # 少なくとも1つの連続休日ウィンドウを選ばせる
        model.Add(
            sum(window_vars) >= 1
        )

    return necessary_consecutive_holidays_length, consecutive_holiday_window_vars
