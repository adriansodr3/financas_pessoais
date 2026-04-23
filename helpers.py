from datetime import date

MONTHS_PT = ["Janeiro","Fevereiro","Marco","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


def fmt_currency(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")


def month_label(year, month):
    return f"{MONTHS_PT[month-1]} {year}"


def prev_month(year, month):
    return (year-1, 12) if month == 1 else (year, month-1)


def next_month(year, month):
    return (year+1, 1) if month == 12 else (year, month+1)


def current_ym():
    t = date.today()
    return t.year, t.month


def today_str():
    return date.today().strftime("%Y-%m-%d")


def fmt_date(s):
    try:
        from datetime import datetime
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return s
