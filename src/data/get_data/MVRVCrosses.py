import chaindl
import pandas as pd

def get_mvrvc():
    url = "https://chainexposed.com/MvrvCross.html"
    df = chaindl.download(url)

    df.index = pd.to_datetime(df.index)

    yest = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)

    if yest in df.index:
        line_yest = df.loc[yest]
    else:
        line_yest = df[df.index < pd.Timestamp.today().normalize()].iloc[-1]

    sth_yest = line_yest["Short Term Holder MVRV 7d MA"]
    lth_yest = line_yest["Long Term Holder MVRV 7d MA"][0]

    return float(sth_yest), float(lth_yest)

if __name__ == "__main__":
    try:
        print(get_mvrvc())
    except Exception as e:
        print(f"Error: {e}")
