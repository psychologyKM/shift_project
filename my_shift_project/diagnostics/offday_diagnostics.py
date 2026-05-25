
def print_offday_workday_diagnostics(
    employees,
    days,
    date_info,
    spreadsheet_url,
    read_worksheet_as_records,
    sunday_count,
):
    """
    固定的に休みになる日数と、workdays_personal_data の指定勤務日数を比較して表示する。
    """

    workdays_records = read_worksheet_as_records(
        spreadsheet_url,
        "workdays_personal_data"
    )

    required_workdays = {
        str(record["name"]).strip(): int(record["workdays"])
        for record in workdays_records
    }

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

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    regular_holiday_records = read_worksheet_as_records(
        spreadsheet_url,
        "regular_holiday_personal_data"
    )

    for record in regular_holiday_records:
        name = str(record["name"]).strip()

        for w in weekdays:
            if int(record[w]) == 1:
                for d in days:
                    if date_info[d]["weekday"] == w:
                        add_forced_off(name, d, f"固定公休:{w}")

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
    print("=== 休み日数と指定勤務日数の事前チェック ===")
    print(f"対象期間の日数: {len(days)}日")
    print(f"全日休みの最低必要日数: {sunday_count + 1}日")
    print()

    for e in employees:
        forced_off_count = len(forced_off_dates[e])
        max_possible_workdays = len(days) - forced_off_count

        print(f"{e}")

        if e in ignore_workdays_employees:
            print("  指定勤務日数: 無視")
        else:
            required = required_workdays.get(e)

            if required is None:
                print("  指定勤務日数: データなし")
            else:
                print(f"  指定勤務日数: {required}日")

                if required > max_possible_workdays:
                    print("  ⚠ 指定勤務日数が、固定休みを除いた勤務可能日数を超えています")

                rough_max_workdays_with_full_day_off = len(days) - max(
                    forced_off_count,
                    sunday_count + 1,
                )

                if required > rough_max_workdays_with_full_day_off:
                    print("  ⚠ 全日休み最低日数も考えると、指定勤務日数が多すぎる可能性があります")

        print(f"  固定的に休みになる日数: {forced_off_count}日")
        print(f"  固定休みを除いた最大勤務可能日数: {max_possible_workdays}日")

        for d, reasons in sorted(forced_off_dates[e].items()):
            reason_text = " / ".join(reasons)
            print(f"    {d}: {reason_text}")

        print()

    return forced_off_dates, required_workdays, ignore_workdays_employees
