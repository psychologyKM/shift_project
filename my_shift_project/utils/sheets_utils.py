
import gspread
from google.auth import default


def get_google_sheet(spreadsheet_url):
    """
    GoogleスプレッドシートのURLからスプレッドシートを開く。
    """

    creds, _ = default()
    gc = gspread.authorize(creds)

    spreadsheet = gc.open_by_url(spreadsheet_url)

    return spreadsheet


def read_worksheet_as_records(spreadsheet_url, worksheet_name):
    """
    指定したワークシートを辞書のリストとして読み込む。

    1行目をヘッダーとして扱う。
    """

    spreadsheet = get_google_sheet(spreadsheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)

    records = worksheet.get_all_records()

    return records


def read_employee_job_table_as_nested_dict(spreadsheet_url, worksheet_name):
    """
    1列目が name、2列目以降が job 名になっているシートを読み込み、
    {job: {employee: value}} の辞書に変換する。

    想定するシート形式:
        name | 朝1 | 早短 | 朝2 | ...
        A | 1   | 0    | 1   | ...
        B | 0   | 0    | 0   | ...
    """

    spreadsheet = get_google_sheet(spreadsheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)

    values = worksheet.get_all_values()

    if len(values) < 2:
        raise ValueError("シートに十分なデータがありません。")

    header = values[0]

    if len(header) < 2:
        raise ValueError("1行目に name と job 名が必要です。")

    name_col = header[0]
    job_names = header[1:]

    if name_col != "name":
        raise ValueError("1列目のヘッダーは 'name' にしてください。")

    employees = []
    all_job_personal_data = {job: {} for job in job_names}

    for row in values[1:]:
        if len(row) == 0:
            continue

        employee = row[0].strip()

        if employee == "":
            continue

        employees.append(employee)

        for job, value in zip(job_names, row[1:]):
            value = value.strip()

            if value == "":
                value = "0"

            all_job_personal_data[job][employee] = int(value)

        # 行が短くて値が足りない場合は0で補う
        if len(row) - 1 < len(job_names):
            missing_jobs = job_names[len(row) - 1:]
            for job in missing_jobs:
                all_job_personal_data[job][employee] = 0

    return employees, job_names, all_job_personal_data