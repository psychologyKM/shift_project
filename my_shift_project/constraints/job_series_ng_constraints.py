
def expand_job_token(token, jobs):
    """
    job_series_NG_personal_data 内の表記を、実際の jobs に展開する。

    例:
        責泊 → 責泊, 責泊兼泊1
        責深 → 責深, 責深兼深1
        休   → 特別扱いなのでここでは展開しない
    """

    token = str(token).strip()

    if token == "休":
        return []

    if token == "責泊":
        return [
            j for j in jobs
            if j == "責泊" or j.startswith("責泊兼")
        ]

    if token == "責深":
        return [
            j for j in jobs
            if j == "責深" or j.startswith("責深兼")
        ]

    # それ以外は基本的に完全一致
    return [
        j for j in jobs
        if j == token
    ]


def add_job_series_ng_constraints(
    model,
    x,
    employees,
    days,
    jobs,
    spreadsheet_url,
    read_worksheet_as_records,
):
    """
    job_series_NG_personal_data シートを読み込み、
    各従業員について、指定された job / 休み の並びが
    対象期間中の任意の位置で出現しないようにする。

    想定するシート形式:
        name | day1 | day2 | day3 | ... | day7
        A| 責泊 | 責泊 | | | | |
        A | 責泊 | 責深 | 責深 | 責深 | | |
        A | 責泊 | 休 | | | | |

    休:
        その日にどのjobにも入っていないこと。

    責泊:
        責泊 および 責泊兼泊1 を含める。

    責深:
        責深 および 責深兼深1 を含める。
    """

    records = read_worksheet_as_records(
        spreadsheet_url,
        "job_series_NG_personal_data"
    )

    day_columns = ["day1", "day2", "day3", "day4", "day5", "day6", "day7"]

    print()
    print("job_series_NG_personal_data:")

    ng_patterns = []

    for record in records:
        # name列がある想定。ただし、先頭列名が空欄の場合にも一応対応する。
        if "name" in record:
            name = str(record["name"]).strip()
        else:
            name_col_candidates = [
                key for key in record.keys()
                if key not in day_columns
            ]

            if len(name_col_candidates) == 0:
                raise ValueError(
                    "job_series_NG_personal_data に name 列が見つかりません。"
                )

            name = str(record[name_col_candidates[0]]).strip()

        if name == "":
            continue

        if name not in employees:
            raise ValueError(
                f"job_series_NG_personal_data にある name '{name}' が employees に存在しません。"
            )

        pattern = []

        for col in day_columns:
            value = str(record.get(col, "")).strip()

            if value == "":
                continue

            pattern.append(value)

        if len(pattern) == 0:
            continue

        ng_patterns.append((name, pattern))

        print(f"  {name}: {pattern}")

    # 各NGパターンについて、対象期間中のすべての開始位置をチェック
    for name, pattern in ng_patterns:
        pattern_length = len(pattern)

        if pattern_length > len(days):
            continue

        for start_idx in range(0, len(days) - pattern_length + 1):
            condition_vars = []

            for offset, token in enumerate(pattern):
                d = days[start_idx + offset]

                condition_var = model.NewBoolVar(
                    f"ng_match_{name}_{start_idx}_{offset}_{token}"
                )

                work_today = sum(
                    x[(name, d, j)]
                    for j in jobs
                )

                if token == "休":
                    # condition_var = 1 なら、その日は勤務なし
                    model.Add(work_today == 0).OnlyEnforceIf(condition_var)

                    # condition_var = 0 なら、その日は勤務あり
                    model.Add(work_today >= 1).OnlyEnforceIf(condition_var.Not())

                else:
                    matched_jobs = expand_job_token(token, jobs)

                    if len(matched_jobs) == 0:
                        raise ValueError(
                            f"NGパターン内の job '{token}' に対応する jobs が見つかりません。"
                        )

                    matched_job_count = sum(
                        x[(name, d, j)]
                        for j in matched_jobs
                    )

                    # condition_var = 1 なら、その日は該当jobに入っている
                    model.Add(matched_job_count >= 1).OnlyEnforceIf(condition_var)

                    # condition_var = 0 なら、その日は該当jobに入っていない
                    model.Add(matched_job_count == 0).OnlyEnforceIf(condition_var.Not())

                condition_vars.append(condition_var)

            # パターンが完全一致することを禁止する
            # つまり、すべての condition_var が 1 になることを禁止
            model.Add(
                sum(condition_vars) <= pattern_length - 1
            )

    return ng_patterns
