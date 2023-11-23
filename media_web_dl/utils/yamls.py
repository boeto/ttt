from pathlib import Path
from typing import Any
import yaml

from media_web_dl.utils.logger import log


class Yamls:
    yaml_path: Path

    def __init__(self, yaml_path: Path) -> None:
        self.yaml_path = yaml_path

    def write_yaml(self, data: Any):
        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        log.debug(f"成功写入文件:{self.yaml_path}")

    def read_yaml(self):
        if not self.yaml_path.exists():
            return
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    def updata_yaml(self, key: str, values: Any):
        old_data = self.read_yaml()
        old_data[key] = values
        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(old_data, f)
