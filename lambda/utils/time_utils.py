from datetime import datetime, date, time as dtime, timedelta

def default_arrival_timestamp(hour: int = 9) -> int:
    """
    Returns a UNIX timestamp for the next occurrence of a given hour.
    Defaults to 9:00 AM today, or tomorrow if past 9:00 AM.
    
    Args:
        hour (int): Hour of day (0-23) for arrival time.

    Returns:
        int: UNIX timestamp
    """
    today = date.today()
    arrival_datetime = datetime.combine(today, dtime(hour=hour))
    if datetime.now() > arrival_datetime:
        arrival_datetime += timedelta(days=1)
    return int(arrival_datetime.timestamp())
