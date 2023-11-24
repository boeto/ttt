import typer

from media_web_dl.core.dl import Dl

app = typer.Typer()
dl = Dl()


@app.command()
def url_file() -> None:
    """
    下载链接文件
    """
    # url = typer.prompt("请输入视频链接")
    url = "https://www.iqiyi.com/v_121nxvu7x98.html"
    # url = "https://v.youku.com/v_show/id_XNjEyNzIxMDQ5Mg==.html"
    dl.url_file(url)


@app.command()
def yk_save_sh_video() -> None:
    """
    下载yk视频文件
    """
    dl.yk_save_sh_video()


@app.command()
def iqy_save_sh_video() -> None:
    """
    下载iqy视频文件
    """
    dl.iqy_save_sh_video()


@app.command()
def tx_save_sh_video() -> None:
    """
    下载tx视频文件
    """
    dl.tx_save_sh_video()


if __name__ == "__main__":
    app()
