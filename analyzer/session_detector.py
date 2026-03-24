"""
Detects current NY time and active trading session from UTC datetime.
"""
from datetime import datetime, timezone, timedelta

# New York UTC offsets
# EDT (summer): UTC-4  (2nd Sun Mar → 1st Sun Nov)
# EST (winter): UTC-5

def get_ny_offset(utc_dt):
    """Return NY UTC offset as timedelta."""
    year = utc_dt.year
    # EDT start: 2nd Sunday of March at 2am
    mar = datetime(year, 3, 1)
    first_sun_mar = mar + timedelta(days=(6 - mar.weekday()) % 7)
    edt_start = first_sun_mar + timedelta(weeks=1, hours=2)
    # EST start: 1st Sunday of November at 2am
    nov = datetime(year, 11, 1)
    first_sun_nov = nov + timedelta(days=(6 - nov.weekday()) % 7)
    est_start = first_sun_nov + timedelta(hours=2)

    if edt_start <= utc_dt.replace(tzinfo=None) < est_start:
        return timedelta(hours=-4)   # EDT
    return timedelta(hours=-5)       # EST


def get_ny_time(utc_dt=None):
    """Return current NY datetime."""
    if utc_dt is None:
        utc_dt = datetime.now(timezone.utc)
    offset = get_ny_offset(utc_dt.replace(tzinfo=None))
    ny_dt = utc_dt + offset
    return ny_dt


def get_session_info(utc_dt=None):
    """
    Returns dict with:
      ny_time_str   — e.g. "02:34 AM EDT"
      session_name  — e.g. "London Open Killzone"
      session_code  — e.g. "LONDON_OPEN"
      description   — brief context about what to expect
    """
    if utc_dt is None:
        utc_dt = datetime.now(timezone.utc)

    offset = get_ny_offset(utc_dt.replace(tzinfo=None))
    ny_dt = utc_dt + offset
    tz_label = "EDT" if offset.total_seconds() == -4*3600 else "EST"
    hour = ny_dt.hour + ny_dt.minute / 60.0   # decimal hour e.g. 9.5 = 9:30 AM

    ny_time_str = ny_dt.strftime(f"%I:%M %p {tz_label}")

    # Session classification by NY hour
    if 0 <= hour < 2:
        code = "NY_MIDNIGHT"
        name = "NY Midnight / Late NY"
        desc = "Post-NY session. Low volume, thin markets. Midnight Open at 12:00 AM NY is a key reference level."
    elif 2 <= hour < 5:
        code = "LONDON_OPEN"
        name = "London Open Killzone (2AM–5AM NY)"
        desc = "High-probability reversal/expansion zone. Expect sweeps of Asian session highs/lows. AMD Manipulation phase often starts here."
    elif 5 <= hour < 7:
        code = "LONDON_MIDDAY"
        name = "London Mid-Session (5AM–7AM NY)"
        desc = "London continuation or consolidation. Lower conviction moves. Watch for retracements to POIs."
    elif 7 <= hour < 10:
        code = "NY_OPEN"
        name = "New York AM Killzone (7AM–10AM NY)"
        desc = "Highest volume session. True directional move of the day. AMD Distribution phase. Highest probability for setups."
    elif 10 <= hour < 12:
        code = "LONDON_CLOSE"
        name = "London Close (10AM–12PM NY)"
        desc = "London positions closing. Often a retracement or reversal of the NY AM move. Lower conviction — be cautious with new entries."
    elif 12 <= hour < 13:
        code = "NY_LUNCH"
        name = "NY Lunch / Dead Zone (12PM–1PM NY)"
        desc = "Lowest volume of the day. Choppy, unpredictable. ICT recommends avoiding trades during this window."
    elif 13 <= hour < 16:
        code = "NY_PM"
        name = "New York PM Session (1PM–4PM NY)"
        desc = "Secondary NY session. Often continuation of AM move or late reversal. Lower volume than AM."
    elif 16 <= hour < 19:
        code = "NY_CLOSE"
        name = "NY Close / Post-Market (4PM–7PM NY)"
        desc = "Market closing. Institutional positions being squared. Gaps may form into next session."
    else:
        code = "ASIAN"
        name = "Asian Session (7PM–12AM NY)"
        desc = "Range accumulation phase. Liquidity builds above/below Asian range for London to sweep. Low volatility expected."

    return {
        "ny_time_str": ny_time_str,
        "session_code": code,
        "session_name": name,
        "session_description": desc,
        "is_killzone": code in ("LONDON_OPEN", "NY_OPEN"),
        "avoid_trading": code in ("NY_LUNCH",),
    }
