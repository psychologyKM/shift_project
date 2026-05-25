
def add_public_holiday_work_or_rest_constraints(
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
    public_holiday_work_or_rest_personal_data シートを読み込み、
    祝日の勤務・休み希望を制約として追加する。

    想定するシート形式:
        name | want_to_rest_public_holiday | want_to_work_public_holiday

    制約:
        - want_to_rest_public_holiday == 1 の人は、祝日に必ず休み
        - want_to_work_public_holiday == 1 の人は、祝日に必ず勤務

    注意:
        ここでの祝日は date_info[d]["is_public_holiday"] == True の日。
        土日を含む休日 date_info[d]["is_holiday"] ではない。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "public_holiday_work_or_rest_personal_data"
    )

    want_to_rest_public_holiday_employees = set()
    want_to_work_public_holiday_employees = set()

    for record in records:
        name = str(record["name"]).strip()

        want_to_rest = int(record.get("want_to_rest_public_holiday", 0))
        want_to_work = int(record.get("want_to_work_public_holiday", 0))

        if want_to_rest == 1 and want_to_work == 1:
            raise ValueError(
                f"{name} は祝日に休みたい・働きたいの両方が1になっています。"
            )

        if want_to_rest == 1:
            want_to_rest_public_holiday_employees.add(name)

        if want_to_work == 1:
            want_to_work_public_holiday_employees.add(name)

    print()
    print("want_to_rest_public_holiday_employees:")
    print(want_to_rest_public_holiday_employees)

    print()
    print("want_to_work_public_holiday_employees:")
    print(want_to_work_public_holiday_employees)

    public_holiday_dates = [
        d for d in days
        if date_info[d]["is_public_holiday"]
    ]

    print()
    print("public_holiday_dates:")
    print(public_holiday_dates)

    # 祝日に休みたい人は、祝日に全jobへ入らない
    for e in employees:
        if e in want_to_rest_public_holiday_employees:
            for d in public_holiday_dates:
                model.Add(
                    sum(x[(e, d, j)] for j in jobs) == 0
                )

    # 祝日に働きたい人は、祝日に何らかのjobへ入る
    for e in employees:
        if e in want_to_work_public_holiday_employees:
            for d in public_holiday_dates:
                model.Add(
                    sum(x[(e, d, j)] for j in jobs) >= 1
                )

    return (
        want_to_rest_public_holiday_employees,
        want_to_work_public_holiday_employees,
        public_holiday_dates,
    )
