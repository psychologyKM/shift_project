import argparse

from ortools.sat.python import cp_model

from utils.calendar_utils import (
    validate_year_month,
    create_date_info_dict,
    count_sundays,
    count_holidays,
)

from utils.sheets_utils import (
    read_worksheet_as_records,
    read_employee_job_table_as_nested_dict,
)

from utils.solver_callbacks import (
    ObjectiveImprovementLogger,
)

from writers.shift_csv_writer import (
    write_shift_schedule_csv,
    write_shift_schedule_to_spreadsheet,
)

# from modulators.modulate_with_special_care import (
#     read_special_care_personal_data,
# )


from diagnostics.offday_diagnostics import (
    print_offday_workday_diagnostics,
)

from diagnostics.consecutive_workday_diagnostics import (
    print_consecutive_workday_diagnostics,
)

from diagnostics.workability_diagnostics import (
    print_workability_with_fixed_off_diagnostics,
)

from constraints.consecutive_workday_constraints import (
    add_consecutive_workdays_limit_constraints,
)


from constraints.basic_constraints import (
    add_one_job_per_day_constraint,
    add_job_skill_constraints,
)

from constraints.night_shift_pattern_constraints import (
    add_night_shift_pattern_constraints,
)

from constraints.weekly_dayoff_constraints import (
    add_weekly_dayoff_constraints,
)

from constraints.regular_workday_constraints import (
    add_regular_workday_constraints,
)

from constraints.job_minimum_constraints import (
    add_job_minimum_constraints,
)

# from constraints.fairness_constraints import (
#     add_fairness_constraints,
# )

from constraints.workday_constraints import (
    add_exact_workdays_constraints,
)

from constraints.public_holiday_constraints import (
    add_public_holiday_work_or_rest_constraints,
)

from constraints.full_day_off_constraints import (
    add_full_day_off_constraints,
)

from constraints.requested_off_constraints import (
    add_requested_off_day_constraints,
)

from constraints.job_maximum_constraints import (
    add_job_maximum_constraints,
)

from constraints.job_min_max_personal_constraints import (
    add_job_min_max_personal_constraints,
)

from constraints.job_series_ng_constraints import (
    add_job_series_ng_constraints,
)

from constraints.if_then_pair_constraints import (
    add_if_then_pair_constraints,
)

from constraints.necessary_consecutive_holidays_constraints import (
    add_necessary_consecutive_holidays_constraints,
)

def main():
    parser = argparse.ArgumentParser(
        description="指定された年月のシフトを作成します。"
    )

    parser.add_argument("year", type=int, help="年。例: 2026")
    parser.add_argument("month", type=int, help="月。例: 5")
    parser.add_argument(
        "--log",
        action="store_true",
        help="診断ログや探索ログを表示します。",
    )

    parser.add_argument(
        "--progress",
        action="store_true",
        help="目的関数が改善したときに進捗ログを表示します。",
    )

    args = parser.parse_args()

    year = args.year
    month = args.month
    enable_log = args.log
    enable_progress = args.progress

    try:
        validate_year_month(year, month)
    except ValueError as e:
        print(f"入力エラー: {e}")
        return

    print(f"{year}年{month}月のシフトの作成を開始します")

    # 日付情報の作成
    date_info = create_date_info_dict(year, month)
    sunday_count = count_sundays(date_info)
    holiday_count = count_holidays(date_info)

    print()
    print("対象期間の日付と曜日:")

    for date_str, info in date_info.items():
        holiday_label = "休日" if info["is_holiday"] else "平日"
        print(f"{date_str}（{info['weekday']}）{holiday_label}")

    print()
    print(f"対象期間に含まれる日曜日の数: {sunday_count}日")
    print(f"対象期間に含まれる休日（土日祝）の数: {holiday_count}日")

    # モデルを生成
    model_ymt = cp_model.CpModel()

    # スプレッドシートURL
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1zlwWyucmmhf7QJ22MFG6Nn_tHrW1Wpw_IPbwiDDPGh4/edit?gid=0#gid=0"

    # ignore_workdays_employees = read_special_care_personal_data(
    #     spreadsheet_url,
    #     read_worksheet_as_records,
    # )

    # 担当可能データを読み込む
    employees, jobs, all_job_personal_data = read_employee_job_table_as_nested_dict(
        spreadsheet_url,
        "all_job_personal_data"
    )

    # 複合jobを追加する
    all_job_personal_data["責泊兼泊1"] = {}
    all_job_personal_data["責深兼深1"] = {}

    for e in employees:
        all_job_personal_data["責泊兼泊1"][e] = (
            all_job_personal_data["責泊"][e]
            * all_job_personal_data["泊1"][e]
        )

        all_job_personal_data["責深兼深1"][e] = (
            all_job_personal_data["責深"][e]
            * all_job_personal_data["深1"][e]
        )

    jobs.append("責泊兼泊1")
    jobs.append("責深兼深1")

    print()
    print("従業員一覧:")
    print(employees)

    print()
    print("job一覧:")
    print(jobs)

    # 日付リスト
    days = list(date_info.keys())

    # 診断
    forced_off_dates, diagnostic_required_workdays, diagnostic_ignore_workdays_employees = (
        print_offday_workday_diagnostics(
            employees,
            days,
            date_info,
            spreadsheet_url,
            read_worksheet_as_records,
            sunday_count,
        )
    )

    diagnostic_required_workdays, diagnostic_maximum_consecutive_workdays = (
        print_consecutive_workday_diagnostics(
            employees,
            days,
            spreadsheet_url,
            read_worksheet_as_records,
        )
    )

    workability_diagnostics = print_workability_with_fixed_off_diagnostics(
        employees,
        days,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 割り当て変数の定義
    # x[(e, d, j)] = 1 なら、従業員 e が日付 d に job j を担当する
    x = {}

    for e in employees:
        for d in days:
            for j in jobs:
                x[(e, d, j)] = model_ymt.NewBoolVar(f"x_{e}_{d}_{j}")

    print()
    print(f"割り当て変数 x の数: {len(x)}")

    ####################
    ###  制約追加ゾーン ###
    ####################

    # 1. 各従業員は1日に1つのjob/shiftにしか入れない
    add_one_job_per_day_constraint(
        model_ymt,
        x,
        employees,
        days,
        jobs,
    )

    # 2. 担当できないjobには割り当てない
    add_job_skill_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        all_job_personal_data,
    )

    # 3. 夜勤パターン制約
    y, night_shift_patterns = add_night_shift_pattern_constraints(
        model_ymt,
        x,
        employees,
        days,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 4. 各jobに固有の必要最低人数を満たす
    add_job_minimum_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 5. 全員が法定休日数 以上の「全日休み」を取る
    full_day_off, jobs_across_midnight, required_full_day_off_count = (
        add_full_day_off_constraints(
            model_ymt,
            x,
            employees,
            days,
            jobs,
            sunday_count,
            spreadsheet_url,
            read_worksheet_as_records,
        )
    )

    # DISCARDED
    # # 6. 各従業員の勤務日数の公平性を確保
    # employee_workdays, fairness_gap = add_fairness_constraints(
    #     model_ymt,
    #     x,
    #     employees,
    #     days,
    #     jobs,
    # )

    # 6. 定期公休曜日制約
    z, weekdays, regular_holiday_personal_data = add_weekly_dayoff_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
        max_dayoff_weekdays=7,
    )

    # 
    # 7. 祝日の勤務・休み希望制約
    (
        want_to_rest_public_holiday_employees,
        want_to_work_public_holiday_employees,
        public_holiday_dates,
    ) = add_public_holiday_work_or_rest_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
    )
    #8. 希望休制約
    requested_off_days = add_requested_off_day_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    #9.  曜日ごとの出勤希望制約
    regular_workday_personal_data = add_regular_workday_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        date_info,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 10. 最大連続勤務日数制約
    maximum_consecutive_workdays = add_consecutive_workdays_limit_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 11.各jobに固有の最大人数を超えない
    job_maximum_workers = add_job_maximum_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )
    
    
    #12. 個人ごと・jobごとの期間内担当回数 min/max 制約
    job_min_max_personal_data = add_job_min_max_personal_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 13. 個人ごとのNG連続パターン制約
    job_series_ng_patterns = add_job_series_ng_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 14. if-then ペア制約
    if_then_pairs = add_if_then_pair_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )

    # 15. 必要な連続休日制約
    (
        necessary_consecutive_holidays_length,
        consecutive_holiday_window_vars,
    ) = add_necessary_consecutive_holidays_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
    )
    
    

    # 100. 各従業員の勤務日数を指定値に完全一致させる
    (
        employee_workdays,
        required_workdays,
        ignore_workdays_employees,
        employee_workdays_diff,
    ) = add_exact_workdays_constraints(
        model_ymt,
        x,
        employees,
        days,
        jobs,
        spreadsheet_url,
        read_worksheet_as_records,
        max_diff=5,
    )

    ####################
    ###  最適化ゾーン    ###
    ####################

    # 勤務日数の指定値からのズレを最小化
    total_workdays_diff = model_ymt.NewIntVar(
        0,
        len(days) * len(employees),
        "total_workdays_diff"
    )
    model_ymt.Add(
        total_workdays_diff == sum(employee_workdays_diff.values())
    )
    model_ymt.Minimize(total_workdays_diff)

    ####################
    ###  求解ゾーン    ###
    ####################

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 8

    if enable_log:
        solver.parameters.log_search_progress = True
    else:
        solver.parameters.log_search_progress = False

    if enable_progress:
        progress_logger = ObjectiveImprovementLogger(
            objective_var=total_workdays_diff,
            label="total_workdays_diff",
            minimize=True,
        )

        status = solver.Solve(model_ymt, progress_logger)
    else:
        status = solver.Solve(model_ymt)

    ####################
    ###  結果表示ゾーン ###
    ####################

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print()
        print("Solution found")
        print("Status:", solver.StatusName(status))
        # print("fairness_gap:", solver.Value(fairness_gap))

        print()
        print()
        print()
        print("Workdays by employee")
        for e in employees:
            actual = solver.Value(employee_workdays[e])

            if e in ignore_workdays_employees:
                print(f"  {e}: {actual} / required ignored")
            else:
                required = required_workdays[e]
                diff = solver.Value(employee_workdays_diff[e])
                print(f"  {e}: {actual} / required {required} / diff {diff}")

        print()
        print("total_workdays_diff:", solver.Value(total_workdays_diff))

        if enable_log:
            print()
            print("Schedule")
            for d in days:
                print(f"\n{d}")

                # 採用された夜勤パターンを表示
                selected_pattern = None
                for pattern_idx in night_shift_patterns:
                    if solver.Value(y[(d, pattern_idx)]) == 1:
                        selected_pattern = pattern_idx
                        break

                print(f"  night pattern: {selected_pattern}")

                # その日のjob割り当てを表示
                for j in jobs:
                    assigned_employees = [
                        e for e in employees
                        if solver.Value(x[(e, d, j)]) == 1
                    ]

                    if assigned_employees:
                        print(
                            f"  {j}: {len(assigned_employees)}人 - "
                            f"{', '.join(assigned_employees)}"
                        )
                    print()

        print()
        print("Weekly dayoff by employee")
        for e in employees:
            selected_weekdays = [
                w for w in weekdays
                if solver.Value(z[(e, w)]) == 1
            ]
            print(f"  {e}: {', '.join(selected_weekdays)}")
                
        print("Full day off by employee")
        for e in employees:
            full_off_dates = [
                d for d in days
                if solver.Value(full_day_off[(e, d)]) == 1
            ]

            print(
                f"  {e}: {len(full_off_dates)}日 "
                f"/ required {required_full_day_off_count}日 - "
                f"{', '.join(full_off_dates)}"
            )

        output_dir = "/content/drive/MyDrive/my_shift_project/outputs"

        if enable_progress:
            progress_callback = IntermediateCsvOnImprovementCallback(
                objective_var=total_workdays_diff,
                x=x,
                employees=employees,
                days=days,
                jobs=jobs,
                date_info=date_info,
                output_dir=output_dir,
                year=year,
                month=month,
                requested_off_days=requested_off_days,
                label="total_workdays_diff",
                minimize=True,
                write_spreadsheet=True,
            )

            status = solver.Solve(model_ymt, progress_callback)

        else:
            status = solver.Solve(model_ymt)

        write_shift_schedule_csv(
            solver,
            x,
            employees,
            days,
            jobs,
            date_info,
            output_dir,
            year,
            month,
            requested_off_days=requested_off_days,
        )

        write_shift_schedule_to_spreadsheet(
            solver,
            x,
            employees,
            days,
            jobs,
            date_info,
            year,
            month,
            requested_off_days=requested_off_days,
        )
        
    else:
        print()
        print("No solution found")
        print("Status:", solver.StatusName(status))


if __name__ == "__main__":
    main()