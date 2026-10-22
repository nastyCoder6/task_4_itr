from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

BASE_DIR = Path(__file__).parent.parent
EUR_TO_USD = 1.2


def read_file():  # TBC
    pass


# STORE 1

# -- BOOKS

with open(BASE_DIR / "data" / "STORE1" / "books.yaml", "r") as file:
    loaded_file = yaml.safe_load(file)
books = pd.DataFrame(loaded_file)
books = books.dropna().drop_duplicates()


books[":unique_authors"] = books[":author"].apply(
    lambda x: frozenset(author.strip() for author in x.split(","))
)

books = books.sort_values(
    by=":unique_authors", key=lambda column: column.map(lambda x: tuple(x))
)

print()
print(f"The number of unique authors: {books[":unique_authors"].nunique()}")

# -- ORDERS

orders = pd.read_parquet(BASE_DIR / "data" / "STORE1" / "orders.parquet")
orders = orders.drop_duplicates()

# I leave "shipping" column for future usage - 25% of missing data

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

daily_revenue = orders.groupby("date")["paid_price"].sum().sort_values(ascending=False)

# print(daily_revenue.head(5))
# -- USERS

users = pd.read_csv(BASE_DIR / "data" / "STORE1" / "users.csv")
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

x = list(daily_revenue.sort_index().keys())
y = list(daily_revenue.sort_index())


fig, ax = plt.subplots()

ax.plot(x, y)

# plt.show()
