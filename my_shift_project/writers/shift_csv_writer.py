
import csv
import os

import gspread
from google.auth import default


def build_shift_schedule_matrix(
    value_getter,
    x,
    employees,
    days,
    jobs,
    date_info,
    requested_off_days=None,
):
    """
    CSV・Googleスプレッドシート出力用の2次元配列を作る。

    value_getter:
        solver.Value または callback.Value のような関数。
    """

    if requested_off_days is None:
        requested_off_days = {}

    rows = []

    # 1行目: 日付
    rows.append(["name"] + days)

    # 2行目: 曜日
    rows.append(["weekday"] + [date_info[d]["weekday"] for d in days])

    # 3行目: 祝日名
    rows.append([
        "public_holiday"
    ] + [
        date_info[d].get("holiday_name") or ""
        for d in days
    ])

    # 4行目以降: 個人別シフト
    for e in employees:
        row = [e]

        for d in days:
            assigned_jobs = [
                j for j in jobs
                if value_getter(x[(e, d, j)]) == 1
            ]

            if assigned_jobs:
                cell_value = " / ".join(assigned_jobs)
            else:
                requested_type = requested_off_days.get((e, d))

                if requested_type in ["有給", "半休"]:
                    cell_value = requested_type
                else:
                    cell_value = "公休"

            row.append(cell_value)

        rows.append(row)

    return rows


def write_rows_to_csv(rows, output_path):
    """
    2次元配列 rows をCSVに保存する。
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return output_path


def write_shift_schedule_csv(
    solver,
    x,
    employees,
    days,
    jobs,
    date_info,
    output_dir,
    year,
    month,
    requested_off_days=None,
):
    """
    求解結果をCSVとして出力する。
    """

    output_path = os.path.join(
        output_dir,
        f"shift_schedule_matrix_{year}_{month:02d}.csv"
    )

    rows = build_shift_schedule_matrix(
        value_getter=solver.Value,
        x=x,
        employees=employees,
        days=days,
        jobs=jobs,
        date_info=date_info,
        requested_off_days=requested_off_days,
    )

    write_rows_to_csv(rows, output_path)

    print()
    print(f"シフト表CSVを出力しました: {output_path}")

    return output_path


def create_shift_schedule_spreadsheet(title):
    """
    新規Googleスプレッドシートを作成する。
    """

    creds, _ = default()
    gc = gspread.authorize(creds)

    spreadsheet = gc.create(title)
    worksheet = spreadsheet.sheet1
    worksheet.update_title("shift_schedule")

    return spreadsheet, worksheet


def update_shift_schedule_worksheet(
    spreadsheet,
    worksheet,
    rows,
    freeze_rows=3,
    freeze_cols=1,
):
    """
    既存の worksheet に rows を書き込む。
    上 freeze_rows 行、左 freeze_cols 列を固定表示にする。
    """

    worksheet.resize(
        rows=len(rows),
        cols=len(rows[0])
    )

    worksheet.clear()

    worksheet.update(
        values=rows,
        range_name="A1"
    )

    spreadsheet.batch_update({
        "requests": [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": worksheet.id,
                        "gridProperties": {
                            "frozenRowCount": freeze_rows,
                            "frozenColumnCount": freeze_cols,
                        },
                    },
                    "fields": (
                        "gridProperties.frozenRowCount,"
                        "gridProperties.frozenColumnCount"
                    ),
                }
            }
        ]
    })


def write_shift_schedule_to_spreadsheet(
    solver,
    x,
    employees,
    days,
    jobs,
    date_info,
    year,
    month,
    requested_off_days=None,
):
    """
    求解結果を新規Googleスプレッドシートとして出力する。
    """

    rows = build_shift_schedule_matrix(
        value_getter=solver.Value,
        x=x,
        employees=employees,
        days=days,
        jobs=jobs,
        date_info=date_info,
        requested_off_days=requested_off_days,
    )

    spreadsheet_title = f"shift_schedule_{year}_{month:02d}"

    spreadsheet, worksheet = create_shift_schedule_spreadsheet(
        spreadsheet_title
    )

    update_shift_schedule_worksheet(
        spreadsheet,
        worksheet,
        rows,
        freeze_rows=3,
        freeze_cols=1,
    )

    print()
    print(f"シフト表Googleスプレッドシートを出力しました: {spreadsheet.url}")

    return spreadsheet.url
