
def add_job_minimum_constraints(
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
    平日・休日ごとに、各jobの必要最低人数を満たす。
    """

    each_single_job_minimum_workers_weekday_records = read_worksheet_as_records(
        spreadsheet_url,
        "each_single_job_minimum_workers_weekday"
    )

    each_single_job_minimum_workers_holiday_records = read_worksheet_as_records(
        spreadsheet_url,
        "each_single_job_minimum_workers_holiday"
    )

    # records を {job: minimum_workers} の辞書に変換
    each_single_job_minimum_workers_weekday = {
        record["job"]: int(record["minimum"])
        for record in each_single_job_minimum_workers_weekday_records
    }

    each_single_job_minimum_workers_holiday = {
        record["job"]: int(record["minimum"])
        for record in each_single_job_minimum_workers_holiday_records
    }

    # 日付ごと・jobごとに、必要最低人数以上を割り当てる
    for d in days:
        is_holiday = date_info[d]["is_holiday"]

        for j in jobs:
            if is_holiday:
                minimum_workers = each_single_job_minimum_workers_holiday.get(j, 0)
            else:
                minimum_workers = each_single_job_minimum_workers_weekday.get(j, 0)

            model.Add(
                sum(x[(e, d, j)] for e in employees) >= minimum_workers
            )
