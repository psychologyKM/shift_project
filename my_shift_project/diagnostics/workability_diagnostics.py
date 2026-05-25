
def print_workability_with_fixed_off_diagnostics(
    employees,
    days,
    date_info,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    固定的に勤務不可の日を考慮したうえで、
    各従業員が最大連勤日数を守りながら指定勤務日数を達成できるかを診断する。

    固定的に勤務不可とみなすもの:
      - requested_off_day_personal_data に載っている希望休
      - regular_holiday_personal_data で 1 が入っている曜日
      - public_holiday_work_or_rest_personal_data で want_to_rest_public_holiday == 1 の人の祝日

    注意:
      - OR-Tools の完全な制約診断ではなく、個人単位の簡易診断
      - job適性、必要人数、夜勤パターンなどは考慮しない
    """

    # 指定勤務日数
    workdays_records = read_worksheet_as_records(
        spreadsheet_url,
        "workdays_personal_data"
    )

    required_workdays = {
        str(record["name"]).strip(): int(record["workdays"])
        for record in workdays_records
    }

    # 最大連勤日数
    consecutive_records = read_worksheet_as_records(
        spreadsheet_url,
        "consecutive_workdays_limit_personal_data"
    )

    maximum_consecutive_workdays = {
        str(record["name"]).strip(): int(record["maximum"])
        for record in consecutive_records
    }

    # special care: 勤務日数制約を無視する人
    special_care_records = read_worksheet_as_records(
        spreadsheet_url,
        "special_care_personal_data"
    )

    ignore_workdays_employees = set()

    for record in special_care_records:
        name = str(record["name"]).strip()
        ignore_workdays = int(record.get("ignore_workdays", 0))

        if ignore_workdays == 1:
            ignore_workdays_employees.add(name)

    # 固定休みの日付を集計
    forced_off_dates = {
        e: {}
        for e in employees
    }

    def add_forced_off(e, d, reason):
        if e not in forced_off_dates:
            return

        if d not in forced_off_dates[e]:
            forced_off_dates[e][d] = []

        forced_off_dates[e][d].append(reason)

    # 1. 希望休
    requested_off_records = read_worksheet_as_records(
        spreadsheet_url,
        "requested_off_day_personal_data"
    )

    for record in requested_off_records:
        name = str(record["name"]).strip()
        month = int(record["month"])
        day = int(record["day"])
        off_type = str(record.get("type", "")).strip()

        for d in days:
            date_obj = date_info[d]["date"]

            if date_obj.month == month and date_obj.day == day:
                add_forced_off(name, d, f"希望休:{off_type}")
                break

    # 2. 固定公休曜日
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    regular_holiday_records = read_worksheet_as_records(
        spreadsheet_url,
        "regular_holiday_personal_data"
    )

    for record in regular_holiday_records:
        name = str(record["name"]).strip()

        for w in weekdays:
            if int(record.get(w, 0)) == 1:
                for d in days:
                    if date_info[d]["weekday"] == w:
                        add_forced_off(name, d, f"固定公休:{w}")

    # 3. 祝日休み希望
    public_holiday_records = read_worksheet_as_records(
        spreadsheet_url,
        "public_holiday_work_or_rest_personal_data"
    )

    for record in public_holiday_records:
        name = str(record["name"]).strip()
        want_to_rest = int(record.get("want_to_rest_public_holiday", 0))

        if want_to_rest == 1:
            for d in days:
                if date_info[d]["is_public_holiday"]:
                    add_forced_off(name, d, "祝日休み希望")

    print()
    print("=== 固定休み配置を考慮した勤務可能性チェック ===")
    print(f"対象期間の日数: {len(days)}日")
    print()

    for e in employees:
        print(e)

        if e in ignore_workdays_employees:
            print("  指定勤務日数: 無視")
            print()
            continue

        if e not in required_workdays:
            print("  指定勤務日数: データなし")
            print()
            continue

        if e not in maximum_consecutive_workdays:
            print("  最大連勤日数: データなし")
            print()
            continue

        required = required_workdays[e]
        maximum = maximum_consecutive_workdays[e]

        if maximum <= 0:
            print(f"  最大連勤日数が不正です: {maximum}")
            print()
            continue

        # 勤務可能日を O、固定休みを X として並べる
        availability_marks = []
        current_block_len = 0
        block_lengths = []

        for d in days:
            if d in forced_off_dates[e]:
                availability_marks.append("X")

                if current_block_len > 0:
                    block_lengths.append(current_block_len)
                    current_block_len = 0
            else:
                availability_marks.append("O")
                current_block_len += 1

        if current_block_len > 0:
            block_lengths.append(current_block_len)

        # 各勤務可能ブロックの中で、最大連勤を守りながら働ける最大日数
        # 例: maximum=5, block_len=10 の場合、最大 9 日勤務可能
        max_workdays_given_blocks = 0

        for block_len in block_lengths:
            max_in_block = block_len - (block_len // (maximum + 1))
            max_workdays_given_blocks += max_in_block

        forced_off_count = len(forced_off_dates[e])

        print(f"  指定勤務日数: {required}日")
        print(f"  最大連勤日数: {maximum}日")
        print(f"  固定休み日数: {forced_off_count}日")
        print(f"  固定休みを除いた勤務可能日数: {len(days) - forced_off_count}日")
        print(f"  勤務可能ブロック長: {block_lengths}")
        print(f"  連勤制約込みの最大勤務可能日数: {max_workdays_given_blocks}日")
        print(f"  カレンダー: {''.join(availability_marks)}")

        if required > max_workdays_given_blocks:
            print("  ⚠ 固定休み配置と連勤制約を考えると、指定勤務日数を満たせません")

        if forced_off_dates[e]:
            print("  固定休み:")
            for d, reasons in sorted(forced_off_dates[e].items()):
                print(f"    {d}: {' / '.join(reasons)}")

        print()

    return {
        "required_workdays": required_workdays,
        "maximum_consecutive_workdays": maximum_consecutive_workdays,
        "forced_off_dates": forced_off_dates,
        "ignore_workdays_employees": ignore_workdays_employees,
    }
