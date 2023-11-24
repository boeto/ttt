from pathlib import Path
from time import sleep
from typing import List, Tuple
import typer
from media_web_dl.core.cookie import cookie_config
from media_web_dl.utils.enums import WebEnum
from media_web_dl.utils.logger import log
from media_web_dl.webs.iqy import Iqy
from media_web_dl.webs.tx import TX
from media_web_dl.webs.yk import YouKu
from media_web_dl.utils.bash import run_bash
from media_web_dl.webs.yk import yk_sh_dir_path, yk_cache_path, yk_history_path
from media_web_dl.webs.iqy import (
    iqy_sh_dir_path,
    iqy_cache_path,
    iqy_history_path,
)
from media_web_dl.webs.tx import (
    tx_sh_dir_path,
    tx_cache_path,
    tx_history_path,
)
from media_web_dl.utils.files import files


class Dl:
    @staticmethod
    def url_file(url: str) -> None:
        if "youku.com" in url:
            yk_cookie = cookie_config.get_cookie(WebEnum.yk)
            youku = YouKu(yk_cookie)
            youku.start(url)
        elif "iqiyi.com" in url:
            iqy_cookie = cookie_config.get_cookie(WebEnum.iqy)
            iqy = Iqy(iqy_cookie)
            iqy.start(url)
        elif "v.qq.com" in url:
            tx_cookie = cookie_config.get_cookie(WebEnum.tx)
            tx = TX(tx_cookie)
            tx.start(url)
        else:
            log.error("暂不支持该链接")

    def single_file(
        self, file_path: Path, cache_path: Path, history_path: Path
    ) -> None:
        file_stem = file_path.stem
        log.debug(f"file_path:{file_path}")
        log.info(f"开始下载: {file_stem}")
        file_cache_path = cache_path / f"{file_stem}"
        log.debug(f"file_cache_path:{file_cache_path}")
        run_bash(str(file_path), self.clean_cache, file_cache_path)
        history_file_path = history_path / f"{file_path.name}"
        files.move_file(file_path, history_file_path)

    def all_list_file(
        self,
        file_list: List[Tuple[Path, str]],
        cache_path: Path,
        history_path: Path,
    ) -> None:
        for file_path in file_list:
            self.single_file(file_path[0], cache_path, history_path)

    def save_sh_video(self, web: WebEnum) -> None:
        if web == WebEnum.yk:
            dir_path = yk_sh_dir_path
            cache_path = yk_cache_path
            history_path = yk_history_path
        elif web == WebEnum.iqy:
            dir_path = iqy_sh_dir_path
            cache_path = iqy_cache_path
            history_path = iqy_history_path
        elif web == WebEnum.tx:
            dir_path = tx_sh_dir_path
            cache_path = tx_cache_path
            history_path = tx_history_path
        else:
            log.error("暂不支持该网站")
            return

        file_list = files.tb_dir_sorted_time(dir_path)

        number_input = typer.prompt(
            """请输入要下载的视频序号,例如3\n如果需要下载全部请输入all\n如果需要退出请输入q\n"""
        )

        if number_input == "q":
            log.info("退出")
            return
        if number_input == "all":
            self.all_list_file(file_list, cache_path, history_path)
            return
        if int(number_input) > len(file_list) or int(number_input) < 1:
            log.error("输入的序号超出范围")
            return

        file_path = file_list[int(number_input) - 1][0]
        self.single_file(file_path, cache_path, history_path)

    def yk_save_sh_video(self) -> None:
        self.save_sh_video(WebEnum.yk)

    def iqy_save_sh_video(self) -> None:
        self.save_sh_video(WebEnum.iqy)

    def tx_save_sh_video(self) -> None:
        self.save_sh_video(WebEnum.tx)

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
