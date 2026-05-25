
def read_special_care_personal_data(
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    special_care_personal_data シートを読み込み、
    特別対応が必要な従業員情報を返す。

    想定するシート形式:
        name | ignore_workdays
        Aさん | 0
        Bさん | 1

    ignore_workdays == 1 の人は、
    勤務日数制約の対象から除外する。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "special_care_personal_data"
    )

    ignore_workdays_employees = set()

    for record in records:
        name = str(record["name"]).strip()
        ignore_workdays = int(record.get("ignore_workdays", 0))

        if ignore_workdays == 1:
            ignore_workdays_employees.add(name)

    print()
    print("ignore_workdays_employees:")
    print(ignore_workdays_employees)

    return ignore_workdays_employees
