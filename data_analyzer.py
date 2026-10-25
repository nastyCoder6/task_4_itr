import pandas as pd


class DataAnalyzer:
    @staticmethod
    def get_unique_authors_count(books):
        return books[":unique_authors"].nunique()

    @staticmethod
    def get_top_author(books, orders):
        top_authors = pd.merge(
            orders, books[[":id", ":unique_authors"]], left_on="book_id", right_on=":id"
        )
        top_author = (
            top_authors.groupby(by=":unique_authors")["quantity"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )

        return list(top_author.keys()[0]) if not top_author.empty else None

    @staticmethod
    def get_top_customer(users, orders):
        top_customers = pd.merge(
            orders, users[["id", "unique_user_id"]], left_on="user_id", right_on="id"
        )
        top_customer = (
            top_customers.groupby(by="unique_user_id")["paid_price"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )

        if top_customer.empty:
            return None, []

        top_uid = top_customer.keys()[0]
        user_id_list = list(users["id"][users["unique_user_id"] == top_uid])
        top_customer_name = users[users["unique_user_id"] == top_uid]["name"].iloc[0]

        return top_customer_name, user_id_list

    @staticmethod
    def get_revenue(orders):
        return (
            orders.groupby("date")["paid_price"]
            .sum()
            .round(2)
            .sort_values(ascending=False)
        )

    @staticmethod
    def filer_df(df, column, value):
        return df[df[column] == value]
