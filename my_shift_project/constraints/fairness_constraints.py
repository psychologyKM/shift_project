
def add_fairness_constraints(model, x, employees, days, jobs):
    """
    各従業員の勤務日数の差を小さくする。
    """

    employee_workdays = {}

    for e in employees:
        employee_workdays[e] = model.NewIntVar(0, len(days), f'workdays_{e}')
        model.Add(
            employee_workdays[e] == sum(x[(e, d, j)] for d in days for j in jobs)
        )

    max_workdays = model.NewIntVar(0, len(days), 'max_workdays')
    min_workdays = model.NewIntVar(0, len(days), 'min_workdays')

    model.AddMaxEquality(max_workdays, list(employee_workdays.values()))
    model.AddMinEquality(min_workdays, list(employee_workdays.values()))

    fairness_gap = model.NewIntVar(0, len(days), 'fairness_gap')
    model.Add(fairness_gap == max_workdays - min_workdays)

    model.Minimize(fairness_gap)

    return employee_workdays, fairness_gap
