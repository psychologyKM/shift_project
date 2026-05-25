
def print_consecutive_workday_diagnostics(
    employees,
    days,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    workdays_personal_data と consecutive_workdays_limit_personal_data の
    単純な整合性を確認する。

    ここでは、希望休・公休・祝日休みなどの位置は考慮せず、
    「指定勤務日数」と「最大連勤日数」だけから見た
    最低限必要な休み日数を確認する。
    """

    workdays_records = read_worksheet_as_records(
        spreadsheet_url,
        "workdays_personal_data"
    )

    required_workdays = {
        str(record["name"]).strip(): int(record["workdays"])
        for record in workdays_records
    }

    consecutive_records = read_worksheet_as_records(
        spreadsheet_url,
        "consecutive_workdays_limit_personal_data"
    )

    maximum_consecutive_workdays = {
        str(record["name"]).strip(): int(record["maximum"])
        for record in consecutive_records
    }

    print()
    print("=== 連勤制約と指定勤務日数の事前チェック ===")
    print(f"対象期間の日数: {len(days)}日")
    print()

    for e in employees:
        print(e)

        if e not in required_workdays:
            print("  指定勤務日数: データなし")
            print()
            continue

        if e not in maximum_consecutive_workdays:
            print("  最大連勤日数: データなし")
            print()
            continue

        workdays = required_workdays[e]
        maximum = maximum_consecutive_workdays[e]

        print(f"  指定勤務日数: {workdays}日")
        print(f"  最大連勤日数: {maximum}日")

        if maximum <= 0:
            print(f"  ⚠ maximum が不正です: {maximum}")
            print()
            continue

        # workdays 日働くために、最大 maximum 連勤を守る場合に最低限必要な休み日数
        # 例: workdays=26, maximum=5 なら、5勤務ごとに休みが必要なので最低5休必要
        minimum_break_days = (workdays - 1) // maximum if workdays > 0 else 0
        minimum_total_days_needed = workdays + minimum_break_days

        print(f"  連勤制約上、最低限必要な休み日数: {minimum_break_days}日")
        print(f"  最低限必要な総日数: {minimum_total_days_needed}日")

        if minimum_total_days_needed > len(days):
            print("  ⚠ 連勤制約と指定勤務日数だけで不可能です")

        print()

    return required_workdays, maximum_consecutive_workdays
    
