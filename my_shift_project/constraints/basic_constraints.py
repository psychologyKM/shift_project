
def add_one_job_per_day_constraint(model, x, employees, days, jobs):
    """
    各従業員は1日に1つのjob/shiftにしか入れない。
    """
    for e in employees:
        for d in days:
            model.Add(
                sum(x[(e, d, j)] for j in jobs) <= 1
            )


def add_job_skill_constraints(model, x, employees, days, jobs, all_job_personal_data):
    """
    担当できないjobには割り当てない。
    """
    for e in employees:
        for d in days:
            for j in jobs:
                if all_job_personal_data[j][e] == 0:
                    model.Add(x[(e, d, j)] == 0)
