import typer
from media_web_dl.utils.files import files
from media_web_dl.utils.logger import log

from media_web_dl.core.cookie import cookieConfig
from media_web_dl.webs.yk import yk_sh_dir_path

app = typer.Typer()


@app.command()
def cookies() -> None:
    """
    查看cookies
    """
    cookies = cookieConfig.get_cookies()
    log.info(f"cookies: {cookies}")


@app.command()
def yk_save_sh() -> None:
    """
    查看yk保存在sh目录下的url_file文件
    """
    files.tb_dir_sorted_time(yk_sh_dir_path)


if __name__ == "__main__":
    app()
