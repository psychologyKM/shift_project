
def add_job_min_max_personal_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    job_min_max_personal_data シートを読み込み、
    個人ごと・jobごとの期間内担当回数に minimum / maximum 制約を追加する。

    想定するシート形式:
        name | job | minimum | maximum
        A | 情報 | 4 | 4
        B | 責泊 | 0 | 2
        ...

    意味:
        例: B, 責泊, 0, 2
        → Bさんが期間中に「責泊」に入る回数は 0回以上2回以下
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "job_min_max_personal_data"
    )

    job_min_max_personal_data = []

    for record in records:
        name = str(record["name"]).strip()
        job = str(record["job"]).strip()
        minimum = int(record["minimum"])
        maximum = int(record["maximum"])

        if name not in employees:
            raise ValueError(
                f"job_min_max_personal_data にある name '{name}' が employees に存在しません。"
            )

        if job not in jobs:
            raise ValueError(
                f"job_min_max_personal_data にある job '{job}' が jobs に存在しません。"
            )

        if minimum > maximum:
            raise ValueError(
                f"{name} / {job} の minimum が maximum を超えています: "
                f"minimum={minimum}, maximum={maximum}"
            )

        job_min_max_personal_data.append({
            "name": name,
            "job": job,
            "minimum": minimum,
            "maximum": maximum,
        })

        assigned_count = sum(
            x[(name, d, job)]
            for d in days
        )

        model.Add(assigned_count >= minimum)
        model.Add(assigned_count <= maximum)

    print()
    print("job_min_max_personal_data:")
    for item in job_min_max_personal_data:
        print(
            f"  {item['name']} / {item['job']}: "
            f"{item['minimum']} - {item['maximum']}"
        )

    return job_min_max_personal_data
