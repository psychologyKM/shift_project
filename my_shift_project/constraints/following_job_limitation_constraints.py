def add_following_job_limitation_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    following_job_limitation シートを読み込み、
    job0 に入った人の翌日の勤務を job1A / job1B のいずれかに制限する。

    想定するシート形式:
        job0 | job1A | job1B
        責泊 | 休 | 責深
        責泊兼泊1 | 休 | 責深
        泊1 | 休 | 深1

    意味:
        ある従業員がある日 job0 に入っていた場合、
        翌日は job1A または job1B のいずれかでなければならない。

    休:
        翌日にどの job にも入らないこと。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "following_job_limitation"
    )

    following_job_limitations = []

    for record in records:
        job0 = str(record["job0"]).strip()
        job1A = str(record["job1A"]).strip()
        job1B = str(record["job1B"]).strip()

        if job0 not in jobs:
            raise ValueError(
                f"following_job_limitation の job0 '{job0}' が jobs に存在しません。"
            )

        for job1 in [job1A, job1B]:
            if job1 != "休" and job1 not in jobs:
                raise ValueError(
                    f"following_job_limitation の翌日job '{job1}' が jobs に存在しません。"
                )

        following_job_limitations.append({
            "job0": job0,
            "job1A": job1A,
            "job1B": job1B,
        })

    print()
    print("following_job_limitations:")
    for item in following_job_limitations:
        print(
            f"  {item['job0']} -> "
            f"{item['job1A']} or {item['job1B']}"
        )

    # 各従業員・各日について、job0 に入っていたら翌日を制限する
    # 最終日は翌日が対象期間外なので、ここでは制約を追加しない
    for e in employees:
        for day_idx in range(len(days) - 1):
            d0 = days[day_idx]
            d1 = days[day_idx + 1]

            for item in following_job_limitations:
                job0 = item["job0"]
                job1A = item["job1A"]
                job1B = item["job1B"]

                allowed_next_terms = []

                for job1 in [job1A, job1B]:
                    if job1 == "休":
                        # 翌日休み = 翌日の全jobが0
                        # これを表す補助変数を作る
                        rest_next_day = model.NewBoolVar(
                            f"follow_rest_{e}_{d0}_{job0}_to_{d1}"
                        )

                        work_next_day = sum(
                            x[(e, d1, j)]
                            for j in jobs
                        )

                        model.Add(work_next_day == 0).OnlyEnforceIf(rest_next_day)
                        model.Add(work_next_day >= 1).OnlyEnforceIf(rest_next_day.Not())

                        allowed_next_terms.append(rest_next_day)

                    else:
                        allowed_next_terms.append(x[(e, d1, job1)])

                # job0 に入っていたら、翌日は allowed_next_terms のどれか
                model.Add(
                    sum(allowed_next_terms) >= 1
                ).OnlyEnforceIf(x[(e, d0, job0)])

    return following_job_limitations
