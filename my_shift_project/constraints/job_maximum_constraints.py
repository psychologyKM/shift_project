
def add_job_maximum_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    each_single_job_maximum_workers シートを読み込み、
    各jobの最大人数を超えないようにする。

    想定するシート形式:
        job | maximum
        責泊 | 1
        責深 | 1
        責遅 | 1
        責早 | 1
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "each_single_job_maximum_workers"
    )

    job_maximum_workers = {
        str(record["job"]).strip(): int(record["maximum"])
        for record in records
    }

    print()
    print("job_maximum_workers:")
    print(job_maximum_workers)

    for j, maximum_workers in job_maximum_workers.items():
        if j not in jobs:
            raise ValueError(
                f"each_single_job_maximum_workers にある job '{j}' が jobs に存在しません。"
            )

        for d in days:
            model.Add(
                sum(x[(e, d, j)] for e in employees) <= maximum_workers
            )

    return job_maximum_workers
