from typing import Any, Dict, Optional
import typer
from media_web_dl.utils.enums import WebEnum
from media_web_dl.utils.yamls import Yamls
from media_web_dl.utils.paths import data_path
from media_web_dl.utils.logger import log

cookie_yaml_path = data_path / "cookie.yaml"
cookie_yaml = Yamls(cookie_yaml_path)


class CookieConfig:
    cookies: Dict[str, Any]

    def __init__(self):
        self.cookies = self.get_cookies()

    def get_cookies(self):
        data = cookie_yaml.read_yaml() or {}
        if not data:
            cookie_yaml.write_yaml(data)
        return data

    def get_cookie(self, name: WebEnum) -> str:
        cookie: str = self.cookies.get(name.value, "")
        if not cookie:
            log.error(f"{name.value}的cookie不存在,请先配置")
            cookie = self.write_cookie(name)
        return cookie

    def write_cookie(
        self,
        name: WebEnum,
        cookie_data: Optional[str] = None,
    ) -> str:
        cookie_input: Optional[str] = None
        if not cookie_data:
            cookie_input = typer.prompt(f"请输入{name.value}的cookie")
        cookie = cookie_input or cookie_data
        while not cookie:
            cookie = typer.prompt(
                f"cookie不能为空, 请重新输入{name.value}的cookie"
            )
        self.cookies[name.value] = cookie
        cookie_yaml.write_yaml(self.cookies)
        log.info(f"{name.value} cookie 更新成功: {cookie}")
        return cookie

    def write_cookies(self):
        for name in WebEnum:
            self.write_cookie(name)
        cookie_yaml.write_yaml(self.cookies)


cookieConfig = CookieConfig()
