from typing import Annotated
import typer
from media_web_dl.core.cookie import cookie_config
from media_web_dl.utils.enums import WebEnum
from media_web_dl.utils.logger import log

app = typer.Typer()


@app.command()
def cookie(
    name: Annotated[WebEnum, typer.Argument(help="输入需要更新的web名字")],
) -> None:
    """
    更新 cookie
    """
    if name not in WebEnum:
        log.error("暂不支持该网站")
        return

    cookie_config.write_cookie(
        name,
    )


if __name__ == "__main__":
    app()
