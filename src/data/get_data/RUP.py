import chaindl
import pandas as pd

def get_rup():
    url = "https://chainexposed.com/RelativeUnrealizedProfit.html"
    df = chaindl.download(url)

    df.index = pd.to_datetime(df.index)

    yest = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)

    if yest in df.index:
        linha_ontem = df.loc[yest]
    else:
        linha_ontem = df[df.index < pd.Timestamp.today().normalize()].iloc[-1]

    rup_ontem = linha_ontem["RUP"]

    return float(rup_ontem)
