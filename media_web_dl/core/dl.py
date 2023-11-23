from pathlib import Path
from time import sleep
import typer
from media_web_dl.core.cookie import cookieConfig
from media_web_dl.utils.enums import WebEnum
from media_web_dl.utils.logger import log
from media_web_dl.webs.yk import YouKu
from media_web_dl.utils.bash import run_bash
from media_web_dl.webs.yk import yk_sh_dir_path, yk_cache_path, yk_history_path
from media_web_dl.utils.files import files


class Dl:
    @staticmethod
    def url_file(url: str) -> None:
        if "youku.com" in url:
            yk_cookie = cookieConfig.get_cookie(WebEnum.yk)
            youku = YouKu(yk_cookie)
            youku.start(url)
        else:
            log.error("暂不支持该链接")

    def yk_save_sh_video(self) -> None:
        file_list = files.tb_dir_sorted_time(yk_sh_dir_path)
        number_input = typer.prompt("请输入要下载的视频序号,例如3")
        file_path = file_list[int(number_input) - 1][0]
        file_stem = file_path.stem
        log.debug(f"file_path:{file_path}")
        log.info(f"开始下载: {file_stem}")
        file_cache_path = yk_cache_path / f"{file_stem}"
        log.debug(f"file_cache_path:{file_cache_path}")
        run_bash(str(file_path), self.clean_cache, file_cache_path)
        files.move_file(file_path, yk_history_path)

    @staticmethod
    def clean_cache(path: Path):
        """
        清理缓存
        """
        log.info("清理缓存...")
        sleep(3)
        if path.exists():
            files.rm(path)
        log.info("清理缓存成功")
