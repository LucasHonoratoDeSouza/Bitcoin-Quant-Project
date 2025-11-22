import chaindl
import pandas as pd

def get_mm():
    url = "https://chainexposed.com/MayerMultiple.html"
    df = chaindl.download(url)

    df.index = pd.to_datetime(df.index)

    yest = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)

    if yest in df.index:
        line_yest = df.loc[yest]
    else:
        line_yest = df[df.index < pd.Timestamp.today().normalize()].iloc[-1]

    mm_yest = line_yest["Mayer Multiple"]

    return float(mm_yest)

if __name__ == "__main__":
    try:
        print(get_mm())
    except Exception as e:
        print(f"Error: {e}")