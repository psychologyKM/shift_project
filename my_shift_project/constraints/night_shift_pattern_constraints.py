
def add_night_shift_pattern_constraints(
    model,
    x,
    employees,
    days,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    night_shift_patterns シートを読み込み、
    各日に夜勤パターンを1つ選び、
    選ばれたパターンに従って各jobの人数を固定する。
    """

    night_shift_pattern_records = read_worksheet_as_records(
        spreadsheet_url,
        "night_shift_patterns"
    )

    # records を {pattern_idx: {job: required_workers}} の形に変換
    night_shift_patterns = {}

    for record in night_shift_pattern_records:
        pattern_idx = str(record["pattern_idx"])
        night_shift_patterns[pattern_idx] = {}

        for j in record:
            if j == "pattern_idx":
                continue

            night_shift_patterns[pattern_idx][j] = int(record[j])

    print()
    print("night_shift_patterns:")
    print(night_shift_patterns)

    # y[(d, pattern_idx)] = 1 なら、日付 d にその夜勤パターンを採用する
    y = {}

    for d in days:
        for pattern_idx in night_shift_patterns:
            y[(d, pattern_idx)] = model.NewBoolVar(
                f'y_{d}_night_pattern_{pattern_idx}'
            )

    # 各日に夜勤パターンを1つだけ選ぶ
    for d in days:
        model.Add(
            sum(y[(d, pattern_idx)] for pattern_idx in night_shift_patterns) == 1
        )

    # 選ばれた夜勤パターンに従って、各jobの割り当て人数を固定する
    for d in days:
        for pattern_idx, pattern in night_shift_patterns.items():
            for j, required_workers in pattern.items():
                model.Add(
                    sum(x[(e, d, j)] for e in employees) == required_workers
                ).OnlyEnforceIf(y[(d, pattern_idx)])

    return y, night_shift_patterns
