import numpy as np
import pandas as pd


class DataCleaner:
    def __init__(self):
        self.eur_to_usd = 1.2
        self.currency_map = {"$": "USD", "€": "EUR", "USD": "USD", "EUR": "EUR"}

    def clean_books(self, books):
        clean = books.dropna().drop_duplicates().copy()
        clean[":unique_authors"] = clean[":author"].apply(
            lambda x: frozenset(author.strip() for author in x.split(","))
        )
        years = pd.to_numeric(clean[":year"], errors="coerce")
        clean[":year"] = np.where(
            years.isna() | (years < 1000), "Unknown", clean[":year"]
        )
        clean[":publisher"] = np.where(
            clean[":publisher"].str.len() <= 1, "Unknown", clean[":publisher"]
        )

        return clean

    def clean_orders(self, orders):
        clean = orders.drop_duplicates().copy()

        clean["currency"] = (
            clean["unit_price"]
            .str.extract(r"([A-Z]{3}|[\$€])")[0]
            .map(self.currency_map)
        )
        clean["unit_price"] = clean["unit_price"].str.replace(
            r"(\d+)[\$¢€](\d+)", r"\1.\2", regex=True
        )
        clean["unit_price"] = pd.to_numeric(
            clean["unit_price"].str.replace(r"[^\d|.]", "", regex=True)
        )

        clean["unit_price_USD"] = np.where(
            clean["currency"] == "EUR",
            clean["unit_price"] * self.eur_to_usd,
            clean["unit_price"],
        )
        clean["paid_price"] = clean["quantity"] * clean["unit_price_USD"]

        clean["timestamp"] = (
            clean["timestamp"]
            .str.replace("A.M.", "AM")
            .str.replace("P.M.", "PM")
            .str.replace(",", ", ")
        )
        clean["timestamp"] = pd.to_datetime(
            clean["timestamp"], format="mixed", errors="coerce", utc=True
        ).dt.floor("s")

        clean["day"] = clean["timestamp"].dt.day
        clean["month"] = clean["timestamp"].dt.month
        clean["year"] = clean["timestamp"].dt.year
        clean["date"] = clean["timestamp"].dt.date

        return clean

    def clean_users(self, users):
        clean = users.drop_duplicates().copy()
        clean["phone"] = clean["phone"].str.replace(r"\D", "", regex=True)
        clean["unique_user_id"] = 0

        clean["address"] = np.where(
            clean["address"].isna() | (clean["address"].str.len() <= 1),
            "Unknown",
            clean["address"],
        )

        group_no_email = clean.groupby(["name", "address", "phone"]).groups
        dup_no_email = [list(val) for val in group_no_email.values() if len(val) > 1]

        group_no_phone = clean.groupby(["name", "address", "email"]).groups
        dup_no_phone = [list(val) for val in group_no_phone.values() if len(val) > 1]

        group_no_address = clean.groupby(["name", "phone", "email"]).groups
        dup_no_address = [
            list(val) for val in group_no_address.values() if len(val) > 1
        ]

        group_no_name = clean.groupby(["phone", "address", "email"]).groups
        dup_no_name = [list(val) for val in group_no_name.values() if len(val) > 1]

        duplicates_merged = dup_no_phone + dup_no_email + dup_no_name + dup_no_address

        unique_id = 1
        for pair in duplicates_merged:
            for index in pair:
                clean.at[index, "unique_user_id"] = unique_id
            unique_id += 1

        single_users = clean[clean["unique_user_id"] == 0].index
        for index in single_users:
            clean.at[index, "unique_user_id"] = unique_id
            unique_id += 1

        return clean
