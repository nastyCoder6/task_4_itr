import json

import pandas as pd
import streamlit as st
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
                        "description": "The exact name of the column to filter on (always map to given description). Depend on the dataset chosen. For 'books': [':id', ':title', ':author', ':genre', ':publisher', ':year', ':unique_authors']. For 'orders': ['id', 'user_id', 'book_id', 'quantity', 'unit_price', 'timestamp', 'shipping', 'currency', 'unit_price_USD', 'paid_price', 'day', 'month', 'year', 'date']. For 'users': ['id', 'name', 'address', 'phone', 'email', 'unique_user_id'].",
                    },
                    "value": {
                        "type": "string",
                        "description": 'The specific value to search for within the selected column. If the value is not numeric then always capitalize the word, for example: "unknown" into "Unknown" or "john doe" into "John Doe"',
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
                        "description": "The name of the dataset.",
                    }
                },
                "required": ["dataset_name"],
            },
        }
        self.code_declaration = {
            "type": "function",
            "name": "execute_code",
            "description": (
                "Executes Python code locally to query and analyze DataFrames. "
                "The code has access to the pandas library as 'pd' and the available DataFrames. "
                "The code MUST assign the final numerical or string answer to a variable named 'final_result'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Valid Python code using pandas. Ensure the code is self-contained "
                            "and does not require external imports other than pandas. "
                            "Example: final_result = len(books[books[':year'] == 2000])"
                        ),
                    }
                },
                "required": ["code"],
            },
        }
        self.tools = [
            self.show_declaration,
            self.filter_declaration,
            self.code_declaration,
        ]

    def _execute_code(self, code: str):
        execution = {
            "books": self.local_datasets["books"],
            "users": self.local_datasets["users"],
            "orders": self.local_datasets["orders"],
            "pd": pd,
        }
        exec(code, {}, execution)

        return execution["final_result"]

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
            system_instruction="""
                                You are a data analysis assistant. You have access to the following pandas DataFrames.
                                Use this schema to write valid queries and code. Note that 'books' columns start with a colon.
                                For uniquess related queries always refer to ':unique_authors' and 'unique_user_id'.

                                1. 'books':
                                - ':id' (int)
                                - ':title' (string)
                                - ':genre' (string)
                                - ':year' (object)
                                - ':publisher' (string)
                                - ':unique_authors' (object)

                                2. 'users':
                                - 'id' (int)
                                - 'name' (string)
                                - 'address' (string)
                                - 'phone' (string)
                                - 'email' (string)
                                - 'unique_user_id' (int)

                                3. 'orders':
                                - 'id' (int)
                                - 'user_id' (int)
                                - 'book_id' (int)
                                - 'quantity' (int)
                                - 'timestamp' (datetime)
                                - 'shipping' (string)
                                - 'currency' (string)
                                - 'unit_price_USD' (float)
                                - 'paid_price' (float)
                                - 'day' (int)
                                - 'month' (int)
                                - 'year' (int)
                                - 'date' (object)
                                
                                """,
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
            case "execute_code":
                st.write("I've generated the query:")
                st.code(args["code"])
                result = self._execute_code(**args)
                final_interaction = self.client.interactions.create(
                    model="gemini-3.5-flash-lite",
                    input=[
                        {
                            "type": "function_result",
                            "name": fc_step.name,
                            "call_id": fc_step.id,
                            "result": [{"type": "text", "text": json.dumps(result)}],
                        }
                    ],
                    tools=self.tools,
                    previous_interaction_id=interaction.id,
                )
                return final_interaction.output_text
            case _:
                return f"Unknown tool: {tool_name}"

        status_message = f"Executed {tool_name} with arguments: {args}"
        return result_df
