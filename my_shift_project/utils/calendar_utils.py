
from datetime import date, timedelta
import jpholiday


WEEKDAY_NAMES_JP = {
    0: "月",
    1: "火",
    2: "水",
    3: "木",
    4: "金",
    5: "土",
    6: "日",
}


def validate_year_month(year, month):
    """
    年・月が正しい値か確認する。
    不正な場合は ValueError を出す。
    """

    if not isinstance(year, int):
        raise ValueError("年は整数で指定してください。")

    if not isinstance(month, int):
        raise ValueError("月は整数で指定してください。")

    if year < 1:
        raise ValueError("年は1以上の整数で指定してください。")

    if month < 1 or month > 12:
        raise ValueError("月は1から12の整数で指定してください。")


def get_shift_period(year, month):
    """
    指定された年月について、
    その月の16日から翌月15日までの日付リストを返す。
    """

    validate_year_month(year, month)

    start_date = date(year, month, 16)

    if month == 12:
        end_date = date(year + 1, 1, 15)
    else:
        end_date = date(year, month + 1, 15)

    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def create_date_info_dict(year, month):
    """
    日付ごとの曜日情報・休日情報を持つ辞書を作成する。
    """

    dates = get_shift_period(year, month)

    date_info = {}

    for d in dates:
        weekday_index = d.weekday()  # 月曜=0, 日曜=6

        is_saturday = weekday_index == 5
        is_sunday = weekday_index == 6
        is_public_holiday = jpholiday.is_holiday(d)

        date_info[d.isoformat()] = {
            "date": d,
            "weekday_index": weekday_index,
            "weekday": WEEKDAY_NAMES_JP[weekday_index],
            "is_saturday": is_saturday,
            "is_sunday": is_sunday,
            "is_public_holiday": is_public_holiday,
            "holiday_name": jpholiday.is_holiday_name(d),
            "is_holiday": is_saturday or is_sunday or is_public_holiday,
        }

    return date_info


def count_sundays(date_info):
    """
    date_info の中に含まれる日曜日の数を数える。
    """

    return sum(1 for info in date_info.values() if info["is_sunday"])


def count_holidays(date_info):
    """
    date_info の中に含まれる休日（土日祝）の数を数える。
    """

    return sum(1 for info in date_info.values() if info["is_holiday"])
