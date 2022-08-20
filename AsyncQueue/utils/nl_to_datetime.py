import parsedatetime
from datetime import datetime


def parse_string_date(phrase: str) -> datetime:
    cal = parsedatetime.Calendar()

    time_struct, _ = cal.parse(phrase)
    return datetime(*time_struct[:6])




if __name__ == "__main__":
    x = parse_string_date("in four days")
    print(x)