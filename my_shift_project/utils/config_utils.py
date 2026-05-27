import os


def read_spreadsheet_url(project_dir):
    """
    master/spreadsheet_url.txt からスプレッドシートURLを読み込む。
    """

    url_path = os.path.join(project_dir, "master", "spreadsheet_url.txt")

    if not os.path.exists(url_path):
        raise FileNotFoundError(
            f"スプレッドシートURLファイルが見つかりません: {url_path}"
        )

    with open(url_path, "r", encoding="utf-8") as f:
        spreadsheet_url = f.read().strip()

    if spreadsheet_url == "":
        raise ValueError(
            f"スプレッドシートURLファイルが空です: {url_path}"
        )

    return spreadsheet_url
