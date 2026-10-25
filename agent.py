import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()


class DataAgent:
    def __init__(self, books: pd.DataFrame, orders: pd.DataFrame, users: pd.DataFrame):
        self.client = genai.Client()
        self.local_datasets = {"books": books, "orders": orders, "users": users}

        self.filter_declaration = {
            "type": "function",
            "name": "filter_data",
            "description": "Filters a specified dataset by returning only the rows where the target column matches a given value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "enum": ["books", "orders", "users"],
                        "description": "The name of the dataset to filter.",
                    },
                    "column_name": {
                        "type": "string",
                        "description": "The exact name of the column to filter on. Valid columns depend on the dataset chosen. For 'books': [':id', ':title', ':author', ':genre', ':publisher', ':year', ':unique_authors']. For 'orders': ['id', 'user_id', 'book_id', 'quantity', 'unit_price', 'timestamp', 'shipping', 'currency', 'unit_price_USD', 'paid_price', 'day', 'month', 'year', 'date']. For 'users': ['id', 'name', 'address', 'phone', 'email', 'unique_user_id'].",
                    },
                    "value": {
                        "type": "string",
                        "description": "The specific value to search for within the selected column.",
                    },
                },
                "required": ["dataset_name", "column_name", "value"],
            },
        }

        self.show_declaration = {
            "type": "function",
            "name": "show_data",
            "description": "Shows a specified dataset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "enum": ["books", "orders", "users"],
                        "description": "The name of the dataset to filter.",
                    }
                },
                "required": ["dataset_name"],
            },
        }

        self.tools = [self.show_declaration, self.filter_declaration]

    def _filter_data(
        self, dataset_name: str, column_name: str, value: str
    ) -> pd.DataFrame:
        if dataset_name not in self.local_datasets:
            raise ValueError(f"Dataset {dataset_name} not found.")
        target_df = self.local_datasets[dataset_name]
        return target_df[target_df[column_name].astype(str) == str(value)]

    def _show_data(self, dataset_name: str) -> pd.DataFrame:
        if dataset_name not in self.local_datasets:
            raise ValueError(f"Dataset {dataset_name} not found.")
        return self.local_datasets[dataset_name]

    def process_query(self, prompt: str) -> pd.DataFrame | None:
        interaction = self.client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
            tools=self.tools,
        )

        try:
            fc_step = next(s for s in interaction.steps if s.type == "function_call")
        except StopIteration:
            return "Question not in scope."

        tool_name = fc_step.name
        args = fc_step.arguments

        match tool_name:
            case "show_data":
                result_df = self._show_data(**args)
            case "filter_data":
                result_df = self._filter_data(**args)
            case _:
                return f"Unknown tool: {tool_name}"

        status_message = f"Executed {tool_name} with arguments: {args}"
        return result_df
