
import time
from ortools.sat.python import cp_model


class ObjectiveImprovementLogger(cp_model.CpSolverSolutionCallback):
    """
    目的関数の値が改善したときだけログを出すコールバック。

    minimize=True の場合:
        objective_value が小さくなったときに表示する。

    minimize=False の場合:
        objective_value が大きくなったときに表示する。
    """

    def __init__(self, objective_var, label="objective", minimize=True):
        super().__init__()

        self.objective_var = objective_var
        self.label = label
        self.minimize = minimize

        self.best_value = None
        self.solution_count = 0
        self.start_time = time.time()

    def OnSolutionCallback(self):
        self.solution_count += 1

        current_value = self.Value(self.objective_var)

        if self.best_value is None:
            improved = True
        elif self.minimize:
            improved = current_value < self.best_value
        else:
            improved = current_value > self.best_value

        if improved:
            self.best_value = current_value
            elapsed = time.time() - self.start_time

            print()
            print("=== objective improved ===")
            print(f"solutions found: {self.solution_count}")
            print(f"elapsed: {elapsed:.2f} sec")
            print(f"{self.label}: {current_value}")
            print(f"best objective bound: {self.BestObjectiveBound()}")
