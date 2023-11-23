import typer
from media_web_dl.cli import show, update, dl

app = typer.Typer()

app.add_typer(show.app, name="show", help="查看配置信息")
app.add_typer(update.app, name="update", help="更新配置信息")
app.add_typer(dl.app, name="dl", help="下载视频文件")

if __name__ == "__main__":
    app()
