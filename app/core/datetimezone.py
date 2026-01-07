from datetime import datetime, timedelta, timezone

def get_thai_now():
    thai_time = datetime.now(timezone(timedelta(hours=7)))
    return thai_time.replace(tzinfo=None)