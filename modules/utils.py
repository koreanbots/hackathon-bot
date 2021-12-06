def parse_second(time: int, as_kor: bool = False) -> str:
    parsed_time = ""
    hour = time // (60 * 60)
    time -= hour * (60 * 60)
    minute = time // 60
    time -= minute * 60
    if hour:
        parsed_time += f"{hour:02d}{'시간 ' if as_kor else ':'}"
    parsed_time += f"{minute:02d}{'분 ' if as_kor else ':'}" if minute else ("" if as_kor else "00:")
    parsed_time += f"{time:02d}{'초' if as_kor else ''}"
    return parsed_time
