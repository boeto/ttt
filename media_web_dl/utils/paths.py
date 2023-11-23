from pathlib import Path

app_path = Path(__file__).resolve().parent.parent
data_path = app_path / "data"
logs_path = app_path / "logs"
output_path = app_path / "output"

data_path.mkdir(parents=True, exist_ok=True)
logs_path.mkdir(parents=True, exist_ok=True)
output_path.mkdir(parents=True, exist_ok=True)
