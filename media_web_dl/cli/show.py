import typer
from media_web_dl.utils.files import files
from media_web_dl.utils.logger import log

from media_web_dl.core.cookie import cookie_config
from media_web_dl.webs.yk import yk_sh_dir_path
from media_web_dl.webs.iqy import iqy_sh_dir_path
from media_web_dl.webs.tx import tx_sh_dir_path

app = typer.Typer()


@app.command()
def cookies() -> None:
    """
    查看cookies
    """
    cookies = cookie_config.get_cookies()
    log.info(f"cookies: {cookies}")


@app.command()
def yk_save_sh() -> None:
    """
    查看yk保存在sh目录下的链接文件
    """
    files.tb_dir_sorted_time(yk_sh_dir_path)


@app.command()
def iqy_save_sh() -> None:
    """
    查看iqy保存在sh目录下的链接文件
    """
    files.tb_dir_sorted_time(iqy_sh_dir_path)


@app.command()
def tx_save_sh() -> None:
    """
    查看tx保存在sh目录下的链接文件
    """
    files.tb_dir_sorted_time(tx_sh_dir_path)


if __name__ == "__main__":
    app()
