import typer

from media_web_dl.core.dl import Dl

app = typer.Typer()
dl = Dl()


@app.command()
def url_file() -> None:
    """
    下载m3u8_url文件, 退出请输入exit
    """
    url = typer.prompt("请输入视频链接")
    dl.url_file(url)


@app.command()
def yk_save_sh_video() -> None:
    """
    查看yk保存在sh目录下的url_file文件
    """
    dl.yk_save_sh_video()


if __name__ == "__main__":
    app()
