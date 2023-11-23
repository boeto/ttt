from datetime import datetime
from pathlib import Path
import shutil
from typing import List, Tuple
from tabulate import tabulate
from media_web_dl.utils.logger import log


class Files:
    @staticmethod
    def list_dir_sorted_time(dir_path: Path) -> List[Tuple[Path, str]]:
        files = dir_path.glob("*")
        sorted_files = sorted(
            (
                (
                    file,
                    datetime.fromtimestamp(file.stat().st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
                for file in files
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_files

    @staticmethod
    def tb_file_list(file_list: list[tuple[Path, str]]) -> None:
        tb = tabulate(
            [
                (i, name[0].name, name[1])
                for i, name in enumerate(file_list, start=1)
            ],
            headers=["编号", "文件名", "修改时间"],
        )
        log.info(f"\n{tb}")

    def tb_dir_sorted_time(self, dir_path: Path) -> List[Tuple[Path, str]]:
        sorted_files_list = self.list_dir_sorted_time(dir_path)
        self.tb_file_list(sorted_files_list)
        return sorted_files_list

    @staticmethod
    def rm(file_path: Path) -> None:
        """
        删除文件、文件夹、空文件夹
        """
        try:
            if not file_path.exists():
                log.info(f"文件不存在,跳过删除: {file_path}")
                return
            elif file_path.is_dir():
                if not any(file_path.iterdir()):
                    file_path.rmdir()
                    log.info(f"--已删除空目录: {file_path}")
                else:
                    shutil.rmtree(file_path)
                    log.info(f"--已删除目录: {file_path}")
            elif file_path.is_file():
                file_path.unlink()
                log.info(f"--已删除文件: {file_path}")

        except Exception as e:
            log.error(f"删除文件失败: {e}")

    @staticmethod
    def move_file(src_path: Path, dst_path: Path) -> None:

        if src_path.exists():
            if not dst_path.parent.exists():
                dst_path.parent.mkdir(parents=True)
                log.info(f"创建目录: {dst_path.parent}")

            shutil.move(
                str(src_path), str(dst_path)
            )  # 需要将 Path 对象转换为字符串
            log.info(f"文件{src_path}已移动到: {dst_path}")
        else:
            log.info(f"源文件不存在: {src_path}")


files = Files()
