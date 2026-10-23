from pathlib import Path

import pandas as pd
import yaml


class DataLoader:
    @staticmethod
    def load_file(file_path):
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
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file ext.: {ext}")
