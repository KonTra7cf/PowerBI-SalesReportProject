import pandas as pd
import datetime as dt
import requests
from functools import reduce


def get_currency_data(code, year):
    start_date = dt.date(year, 1, 1).strftime("%Y-%m-%d")
    end_date = dt.date(year, 12, 31).strftime("%Y-%m-%d")

    url = f"http://api.nbp.pl/api/exchangerates/rates/a/{code}/{start_date}/{end_date}/"

    r = requests.get(url)

    data = pd.DataFrame(r.json()["rates"]).iloc[:, 1:]

    return data


company_currency = "inr"

currency_codes = [company_currency, "usd", "krw"]

start_year = 2017
end_year = 2021

data_frames = []

for code in currency_codes:
    data = pd.concat(
        [get_currency_data(code, year) for year in range(start_year, end_year + 1)]
    )

    data.rename(columns={"effectiveDate": "Date", "mid": f"{code}/pln"}, inplace=True)

    data_frames.append(data)

df_merged = reduce(
    lambda left, right: pd.merge(left, right, on=["Date"], how="outer"), data_frames
)

for code in currency_codes[1:]:
    df_merged[f"{code}/{company_currency}"] = (
        df_merged[f"{code}/pln"] / df_merged[f"{company_currency}/pln"]
    )


remove_cols = [col for col in df_merged.columns if col.endswith("pln")]

df_merged.drop(columns=remove_cols, inplace=True)

dataset = df_merged.groupby(pd.PeriodIndex(df_merged["Date"], freq="M")).mean(
    numeric_only=True
)

dataset.index = dataset.index.to_timestamp().to_pydatetime()

dataset.reset_index(level=0, inplace=True)

del df_merged
del data
