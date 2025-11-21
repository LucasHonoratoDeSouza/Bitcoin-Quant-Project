import chaindl
import pandas as pd

def get_mvrvc():
    url = "https://chainexposed.com/MvrvCross.html"
    df = chaindl.download(url)

    df.index = pd.to_datetime(df.index)

    yest = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)

    if yest in df.index:
        linha_ontem = df.loc[yest]
    else:
        linha_ontem = df[df.index < pd.Timestamp.today().normalize()].iloc[-1]

    sth_ontem = linha_ontem["Short Term Holder MVRV 7d MA"]
    lth_ontem = linha_ontem["Long Term Holder MVRV 7d MA"][0]

    floatsth, floatlth = float(sth_ontem), float(lth_ontem)

    return floatsth, floatlth

print(get_mvrvc())