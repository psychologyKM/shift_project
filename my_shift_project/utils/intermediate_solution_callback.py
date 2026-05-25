
import os
import time

from ortools.sat.python import cp_model

from writers.shift_csv_writer import (
    build_shift_schedule_matrix,
    write_rows_to_csv,
    create_shift_schedule_spreadsheet,
    update_shift_schedule_worksheet,
)


class IntermediateCsvOnImprovementCallback(cp_model.CpSolverSolutionCallback):
    """
    目的関数が改善したタイミングで、
    intermediate_shift_schedule.csv と
    intermediate用Googleスプレッドシートを上書き更新する callback。
    """

    def __init__(
        self,
        objective_var,
        x,
        employees,
        days,
        jobs,
        date_info,
        output_dir,
        year,
        month,
        requested_off_days=None,
        label="objective",
        minimize=True,
        write_spreadsheet=True,
    ):
        super().__init__()

        self.objective_var = objective_var
        self.x = x
        self.employees = employees
        self.days = days
        self.jobs = jobs
        self.date_info = date_info
        self.output_dir = output_dir
        self.year = year
        self.month = month
        self.requested_off_days = requested_off_days or {}

        self.label = label
        self.minimize = minimize
        self.write_spreadsheet = write_spreadsheet

        self.best_value = None
        self.solution_count = 0
        self.start_time = time.time()

        os.makedirs(self.output_dir, exist_ok=True)

        self.csv_output_path = os.path.join(
            self.output_dir,
            "intermediate_shift_schedule.csv"
        )

        self.intermediate_spreadsheet = None
        self.intermediate_worksheet = None
        self.intermediate_spreadsheet_url = None

        if self.write_spreadsheet:
            title = f"intermediate_shift_schedule_{year}_{month:02d}"
            (
                self.intermediate_spreadsheet,
                self.intermediate_worksheet,
            ) = create_shift_schedule_spreadsheet(title)

            self.intermediate_spreadsheet_url = self.intermediate_spreadsheet.url

            print()
            print(
                "intermediate用Googleスプレッドシートを作成しました: "
                f"{self.intermediate_spreadsheet_url}"
            )

    def OnSolutionCallback(self):
        self.solution_count += 1

        current_value = self.Value(self.objective_var)

        if self.best_value is None:
            improved = True
        elif self.minimize:
            improved = current_value < self.best_value
        else:
            improved = current_value > self.best_value

        if not improved:
            return

        self.best_value = current_value
        elapsed = time.time() - self.start_time

        print()
        print("=== objective improved ===")
        print(f"solutions found: {self.solution_count}")
        print(f"elapsed: {elapsed:.2f} sec")
        print(f"{self.label}: {current_value}")
        print(f"best objective bound: {self.BestObjectiveBound()}")

        rows = build_shift_schedule_matrix(
            value_getter=self.Value,
            x=self.x,
            employees=self.employees,
            days=self.days,
            jobs=self.jobs,
            date_info=self.date_info,
            requested_off_days=self.requested_off_days,
        )

        # CSVを上書き
        write_rows_to_csv(rows, self.csv_output_path)
        print(f"intermediate CSVを更新しました: {self.csv_output_path}")

        # スプレッドシートを更新
        if self.write_spreadsheet:
            update_shift_schedule_worksheet(
                self.intermediate_spreadsheet,
                self.intermediate_worksheet,
                rows,
                freeze_rows=3,
                freeze_cols=1,
            )

            print(
                "intermediate Googleスプレッドシートを更新しました: "
                f"{self.intermediate_spreadsheet_url}"
            )
