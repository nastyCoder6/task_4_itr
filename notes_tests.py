from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

BASE_DIR = Path(__file__).parent
EUR_TO_USD = 1.2
STORE = "STORE1"


# to sepparate into 3 parts + pipeline
class DataProccessor:
    def __init__(self) -> None:
        pass

    def load_file(self, file_path):
        path = Path(file_path)
        ext = path.suffix.lower()

        readers = {
            ".csv": pd.read_csv,
            ".xlsx": pd.read_excel,
            ".xls": pd.read_excel,
            ".json": pd.read_json,
            ".parquet": pd.read_parquet,
            ".xml": pd.read_xml,
        }

        if ext in readers:
            return readers[ext](path)

        elif ext in [".yaml", ".yml"]:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return pd.DataFrame(data)

        else:
            raise ValueError(f"Unsupported file ext.: {ext}")

    def format_books(self, books):
        clean_books = books.dropna().drop_duplicates()
        clean_books[":unique_authors"] = clean_books[":author"].apply(
            lambda x: frozenset(author.strip() for author in x.split(","))
        )

        sorted_books = clean_books.sort_values(
            by=":unique_authors", key=lambda column: column.map(lambda x: tuple(x))
        )
        return sorted_books

    def format_users():
        pass

    def format_orders(self, orders):
        orders = orders.drop_duplicates()
        pass

    def get_top_revenue():
        pass

    def get_unique_users():
        pass

    def get_unique_authors(self, books):
        return books[":unique_authors"].nunique()

    def get_top_author():
        pass

    def get_top_buyer():
        pass

    def get_revenue_chart(self, orders):
        return orders.groupby("date")["paid_price"].sum().sort_values(ascending=False)


# -- BOOKS


proccessor = DataProccessor()
path = BASE_DIR / "data" / STORE

books = proccessor.load_file(path / "books.yaml")
orders = proccessor.load_file(path / "orders.parquet")
users = proccessor.load_file(path / "users.csv")

formatted_books = proccessor.format_books(books)
formatted_orders = proccessor.format_books(orders)
formatted_users = proccessor.format_books(users)

unique_authors = proccessor.get_unique_authors(formatted_books)
print(f"The number of unique authors: {unique_authors}")

# -- ORDERS


# unit_price fixing

currency = {"$": "USD", "€": "EUR", "USD": "USD", "EUR": "EUR"}
orders["currency"] = (
    orders["unit_price"].str.extract(r"([A-Z]{3}|[\$€])")[0].map(currency)
)

orders["unit_price"] = orders["unit_price"].str.replace(
    r"(\d+)[\$¢€](\d+)", r"\1.\2", regex=True
)

orders["unit_price"] = pd.to_numeric(
    orders["unit_price"].str.replace(r"[^\d|.]", "", regex=True)
)

orders["unit_price_USD"] = np.where(
    orders["currency"] == "EUR",
    orders["unit_price"] * EUR_TO_USD,
    orders["unit_price"],
)

orders["paid_price"] = orders["quantity"] * orders["unit_price_USD"]

# timestamp fixing


orders["timestamp"] = (
    orders["timestamp"]
    .str.replace("A.M.", "AM")
    .str.replace("P.M.", "PM")
    .str.replace(",", ", ")
)
orders["timestamp"] = pd.to_datetime(
    orders["timestamp"], format="mixed", errors="coerce", utc=True
).dt.floor("s")


orders["day"] = orders["timestamp"].dt.day
orders["month"] = orders["timestamp"].dt.month
orders["year"] = orders["timestamp"].dt.year
orders["date"] = orders["timestamp"].dt.date


# -- USERS

users = users.drop_duplicates()

# phone fixing
users["phone"] = users["phone"].str.replace(r"\D", "", regex=True)

# UNIQUE users
users["unique_user_id"] = 0
# without email
group_without_email = users.groupby(["name", "address", "phone"]).groups
duplicated_without_email = [
    list(value) for value in group_without_email.values() if len(value) > 1
]


# without phone
group_without_phone = users.groupby(["name", "address", "email"]).groups
duplicated_without_phone = [
    list(value) for value in group_without_phone.values() if len(value) > 1
]
# without address
group_without_address = users.groupby(["name", "phone", "email"]).groups
duplicated_without_address = [
    list(value) for value in group_without_address.values() if len(value) > 1
]
# without name
group_without_name = users.groupby(["phone", "address", "email"]).groups
duplicated_without_name = [
    list(value) for value in group_without_name.values() if len(value) > 1
]

duplicates_merged = (
    duplicated_without_phone
    + duplicated_without_email
    + duplicated_without_name
    + duplicated_without_address
)

unique_user_id = 1
for pair in duplicates_merged:
    for index in pair:
        users.at[index, "unique_user_id"] = unique_user_id
    unique_user_id += 1

single_users = users[users["unique_user_id"] == 0].index
for index in single_users:
    users.at[index, "unique_user_id"] = unique_user_id
    unique_user_id += 1

print(f"The number of unique users: {users["unique_user_id"].nunique()}")
# --

top_authors = pd.merge(
    orders, books[[":id", ":unique_authors"]], left_on="book_id", right_on=":id"
)


top_author = (
    top_authors.groupby(by=":unique_authors")["quantity"]
    .sum()
    .sort_values(ascending=False)
    .head(1)
)


print(f"Top author(s): {list(top_author.keys()[0])}")

top_customers = pd.merge(
    orders, users[["id", "unique_user_id"]], left_on="user_id", right_on="id"
)

top_customer = (
    top_customers.groupby(by="unique_user_id")["paid_price"]
    .sum()
    .sort_values(ascending=False)
    .head(1)
)


user_id_list = list(users["id"][users["unique_user_id"] == top_customer.keys()[0]])
top_customer_name = users[users["unique_user_id"] == top_customer.keys()[0]][
    "name"
].iloc[0]

print(f"Top customer: {top_customer_name}, as: {user_id_list}")

# PLOT

# x = list(daily_revenue.sort_index().keys())
# y = list(daily_revenue.sort_index())


# fig, ax = plt.subplots()

# ax.plot(x, y)

# plt.show()
