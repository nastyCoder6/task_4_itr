from pathlib import Path

from data_analyzer import DataAnalyzer
from data_cleaner import DataCleaner
from data_loader import DataLoader


class DataPipeline:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.cleaner = DataCleaner()
        self.analyzer = DataAnalyzer()

    def run(self):
        books_raw = DataLoader.load_file(self.data_dir / "books.yaml")
        orders_raw = DataLoader.load_file(self.data_dir / "orders.parquet")
        users_raw = DataLoader.load_file(self.data_dir / "users.csv")

        books = self.cleaner.clean_books(books_raw)
        orders = self.cleaner.clean_orders(orders_raw)
        users = self.cleaner.clean_users(users_raw)

        metrics = {
            "unique_authors": self.analyzer.get_unique_authors_count(books),
            "top_author": ", ".join(self.analyzer.get_top_author(books, orders)),
            "top_customer": self.analyzer.get_top_customer(users, orders),
            "total_unique_users": users["unique_user_id"].nunique(),
            "top_5_revenue": self.analyzer.get_revenue(orders)
            .head(5)
            .to_frame()
            .style.format({"paid_price": "${}"}),
            "daily_revenue": self.analyzer.get_revenue(orders),
        }

        return books, orders, users, metrics


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    STORE_DIR = BASE_DIR / "data" / "STORE1"

    pipeline = DataPipeline(STORE_DIR)
    clean_books, clean_orders, clean_users, report = pipeline.run()

    print(f"The number of unique authors: {report['unique_authors']}")
    print(f"Top author(s): {report['top_author']}")
    print(f"Top customer: {report['top_customer'][0]}, as: {report['top_customer'][1]}")
    print(f"The number of unique users: {report['total_unique_users']}")
