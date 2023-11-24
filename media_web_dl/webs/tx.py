import base64
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any, List
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from tabulate import tabulate
import typer
from wasmer_compiler_cranelift import Compiler
from wasmer import (
    Store,
    Function,
    Memory,
    Module,
    ImportObject,
    engine,
    Instance,
    Table,
    FunctionType,
    Type,
)
from media_web_dl.core.cookie import cookie_config
from media_web_dl.utils.enums import WebEnum
from media_web_dl.utils.logger import log
from media_web_dl.utils.wasm import wasmBinaryFile
from media_web_dl.utils.paths import output_path
from media_web_dl.webs.common import m3u8_bin_path, select_prompt
from media_web_dl.utils.tools import (
    rsa_dec,
    aes_decrypt,
    djb2Hash,
    b64decode,
    dealck,
    get_size,
)


# paths
tx_output_path = output_path / "tx"

tx_cache_path = tx_output_path / "cache"
tx_save_path = tx_output_path / "save"
tx_url_file_path = tx_output_path / "url_file"
tx_history_path = tx_output_path / "history"

tx_sh_dir_path = tx_url_file_path / "sh"
tx_txt_dir_path = tx_url_file_path / "txt"
tx_m3u8_dir_path = tx_url_file_path / "m3u8"


class Txckey:
    def __init__(self):
        appCodeName = "Mozilla"
        appName = "Netscape"
        appVersion = "Win32"
        platform = ("Win32",)
        try:
            self.appCodeName = appCodeName
            self.appName = appName
            self.appVersion = appVersion
            self.platform = platform
            self.userAgent = (
                "mozilla/5.0 (windows nt 10.0; win64; x64) applewebKit/537.36"
                " (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            )
            self.key = "2A5AA60178AA6C8DA662E443773A6C4E"
            self.iv = "CFAC216FAA2D396013575D4055C63350"
            self.ptrs = []
            self.pr = None
            self.table = None
            self.memory = Any
            self.func = {}

            if wasmBinaryFile.startswith(
                "data:application/octet-stream;base64,"
            ):
                wasm_file = base64.b64decode(wasmBinaryFile.split(",")[1])
            else:
                wasm_file = Path(wasmBinaryFile).read_bytes()
            self.wasm_file = wasm_file
            self.store = Store(engine.JIT(Compiler))
            self.module = Module(self.store, self.wasm_file)
            self.import_object = ImportObject()
            self.register()
            self.asm = Instance(self.module, self.import_object)
            self.exports = self.asm.exports
            self.gen_export_object()
            self.gen_func()
        except Exception as e:
            log.error(f"{e}")
            raise e

    def gen_func(self):
        func = {
            "free": self.func["2zQ"],
            "malloc": self.func["tCj"],
        }
        self.func.update(func)

    def malloc(self, length):
        ptr = self.func["malloc"](length)
        self.ptrs.append(ptr)
        return ptr

    def free(self, ptr):
        if isinstance(ptr, list):
            for i in ptr:
                self.free(i)
        else:
            self.func["free"](ptr)

    def free_all(self):
        self.free(self.ptrs)
        self.ptrs = []

    def ccall(self, func_name: str, returnType: "type", *args):
        def convertReturnValue(_ptr: int):
            if returnType == str:
                return self.UTF8ToString(_ptr)
            elif returnType == bool:
                return bool(returnType)
            return _ptr

        _args = []
        for arg in args:
            if isinstance(arg, str):
                max_write_length = len(arg) + 64
                ptr = self.malloc(max_write_length)
                if len(arg) >= 30:
                    self.pr = ptr
                self.stringToUTF8(arg, ptr, max_write_length)
                _args.append(ptr)
            elif isinstance(arg, list):
                max_write_length = len(arg) + 8
                ptr = self.malloc(max_write_length)
                self.writeArrayToMemory(arg, ptr, max_write_length)
                _args.append(ptr)
            else:
                _args.append(arg)
        ptr = self.func[func_name](*_args)
        ret = convertReturnValue(ptr)
        return ret

    @staticmethod
    def _abort():
        pass

    def _emscripten_memcpy_big(self, dest: int, src: int, num: int):
        if num is None:
            num = len(self.memory.uint8_view()) - 1
        self.memory.uint8_view()[dest : dest + num] = self.memory.uint8_view()[  # type: ignore # noqa: E501
            src : src + num
        ]

    def stringToUTF8(self, data: str, ptr: int, max_write_length: int):
        _data = data.encode("utf-8")
        write_length = len(_data)
        if write_length == 0:
            self.memory.uint8_view()[ptr] = 0  # type: ignore
        _data = _data + b"\0" * (max_write_length - write_length)
        uint8 = self.memory.uint8_view(offset=ptr)  # type: ignore
        uint8[0:max_write_length] = _data

    def UTF8ToString(self, ptr: int) -> str:
        if ptr > 0:
            _memory = self.memory.uint8_view(offset=ptr)  # type: ignore
            data = []
            index = 0
            while _memory[index] != 0:
                data.append(_memory[index])
                index += 1
            return bytes(data).decode("utf-8")
        else:
            return ""

    def writeArrayToMemory(
        self, array: List[Any], ptr: int, max_write_length: int
    ):
        array = array + [0] * (max_write_length - len(array))
        self.memory.uint8_view()[  # type: ignore
            ptr, ptr + max_write_length
        ] = array  # noqa: E501

    def _emscripten_resize_heap(self, param_0: int) -> int:
        return 0

    def gettm(self) -> float:
        # -> "f64":
        return float(time.time())

    def EjW(self, param_0: int) -> int:
        return 0

    def gen_import_object(self):
        a = {
            "6Gj": Function(self.store, self._abort),
            "xuX": Function(self.store, self._emscripten_memcpy_big),
            "2fb": Function(
                self.store, self.gettm, FunctionType([], [Type.F64])
            ),
            "EjW": Function(self.store, self.EjW),
        }
        tximport = {
            "hc2": a,
        }
        return tximport

    def gen_export_object(self):
        func = dict()
        for k, v in self.exports:
            if isinstance(v, Function):
                func[k] = v
            elif isinstance(v, Memory):
                setattr(self, "memory", v)
            elif isinstance(v, Table):
                setattr(self, "table", v)
            # log.info(k, v.type)
        self.func = func

    def register(self):
        for i in self.gen_import_object():
            self.import_object.register(i, self.gen_import_object()[i])

    def __del__(self):
        self.free_all()
        del self.ptrs

    def gen_key(self, *args):
        return self.ccall("otm", str, *args)

    def ckey(
        self,
    ):
        pass

    def aesenc(self, data: str) -> str:
        key = bytes.fromhex(self.key)
        iv = bytes.fromhex(self.iv)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_bytes = pad(data.encode("utf-8"), 16)  # Fix: Encode data as bytes
        return cipher.encrypt(data_bytes).hex().upper()

    def aesdec(self, data: str, key=None, iv=None) -> str:
        key = bytes.fromhex(self.key)
        iv = bytes.fromhex(self.iv)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data_bytes = bytes.fromhex(data)
        return unpad(cipher.decrypt(data_bytes), 16).decode("utf-8")

    @staticmethod
    def get_hash(s):
        h = 0
        for c in s:
            h = (h << 5) - h + ord(c)
        return str(h & 0xFFFFFFFF)

    def ckey81(
        self,
        vid,
        tm,
        appVer="3.5.57",
        guid="",
        platform="10201",
        url="https://v.qq.com/x/cover/mzc00200b4jsdq6/l00469csvi7.html",
    ):
        url = url[0:48]
        navigator = self.userAgent[0:48]
        appCodeName = self.appCodeName
        appName = self.appName
        platforma = self.platform
        s = (
            "|"
            + "|".join(
                [
                    vid,
                    tm,
                    "mg3c3b04ba",
                    appVer,
                    guid,
                    platform,
                    url,
                    navigator,
                    url,
                    appCodeName,
                    appName,
                    platforma[0],  # Fix: Access the first element of the tuple
                    "00",
                ]
            )
            + "|"
        )
        s = "|" + self.get_hash(s) + s
        return s

    @staticmethod
    def roundstr(mun: int = 32):
        return "".join(
            random.sample(
                "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba1234567890",  # noqa: E501
                mun,
            )
        )

    @staticmethod
    def md5str(a: str):
        return hashlib.md5(a.encode()).hexdigest()

    def ckey85(self, vid, appVer="1.26.3", guid="", platform="10201", h38=""):
        data = {
            "vid": vid,
            "nonce": "",
            "rand": "",
            "appVer": appVer,
            "guid": guid,
            "platform": platform,
        }
        ts = str(int(time.time()))
        data["ts"] = ts
        nonce = self.roundstr(11)
        rand = self.md5str(nonce + "1234")[:8]
        data["rand"] = rand
        data["nonce"] = nonce
        ckey = json.dumps(data, separators=(",", ":"))
        enc = self.aesenc(ckey)
        ckey = "--01" + enc
        return ckey

    def ckey92(
        self,
        tm,
        vid,
        appVer="1.28.2",
        guid="",
        h38="",
        url="https://v.qq.com/x/cover/mzc002006w8m6hk/u0047t48n6f.html",
        platform=10201,
        l='{"cp":"59zexbw7hg","csal":["m5h0zchrh5"]}',
        r='{"ea":3,"spa":1,"hwdrm":4,"hwacc":1}',
    ):
        url = url[0:48]
        s = (
            url
            + "|mozilla/5.0 (windows nt 10.0; win64; x64)"
            " applew|https://v.qq.com/channel/tv|Mozilla|Netscape|Win32"
        )
        data = [platform, appVer, vid, "", guid, s, l, r, h38, int(tm)]
        ckey = self.gen_key(*data).split("|")
        for i in ckey:
            if ckey.count(i) == 1:
                ckey = i
                break
            if i == ckey[-1]:
                ckey = ckey[5]
        return ckey


class TX:
    def __init__(self, ck):
        self.ckey = Txckey()
        self.guid = None
        self.h38 = None
        self.ck = ck
        self.key = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            + "MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAOG98XlIossYaXk4RHWOZutQEo1wvC4GHMNFBsYhGVbJgPVAF7SM6rPIkC/efoJ9qHYPcYGhh5LdB/FZkBkj8neeKT76+7CZkMYoolYS5gGLg4IgxTDS7uVoKMRLXQSKJxfEGLDlGKZ+oqQmW7hVUMTsYnsn+6WTk+P4FRTWO2uPAgMBAAECgYBKBbDS5mCLXFvppeu86I8TBlSvEJKEPPjdhxrriRr3/GdPBE9BoxurDE9LgxfUzkOZQwMjUMZWACiEmavIsqLkvM2Ld7WCQ6oiO739xZkQsgX/M0X7f1lcldLB2kHEsglWWexGoK68KD99HufHK+6QAnIL+AVhpE7cDXCmtK++AQJBAPGO6as8+3Vnm10ruCPt23FmrZlxpKA5LVzW9m0adPFWbPMJJFvI0oI9eJVhMYa9uFcRhdO0YSyrkUKvoAS7OIECQQDvPPWvy719Z5cIjE2yFh4DKS5JRZnPZZia2XGnOotbwEt6SFFFqASyR5xfh+1gjbaJ/6mQlli0YWvjWK8ylRwPAkEA4epkFffBwer1Pi0+WbQCcUuzfnfvnL389ABDloSQ7ImE+cQKEiF+57nwBd1RwY+8UQodXIMuAuYuw+yXPvWOgQJAJyPQBjzM+ZFTEmDx7SrVKis4mWA7s8SpXNwqTfO0DQS+1Hi0YzMD4a75lF+GpH9K1/Tt5uvSA2DU59MAhsQCXQJABelyNLFk6bf4n8CYAlOCZ7JCh3pUfbZ5mkuj6VmROzjXzRrT9B/tezNK7nEeUstVTiwl/DMXYCCwVXkLCvq9Bw==\n"  # noqa: E501
            + "-----END RSA PRIVATE KEY-----\n"
        )
        self.logintoken = {
            "access_token": "",
            "appid": "",
            "vusession": "",
            "openid": "",
            "vuserid": "",
            "video_guid": "",
            "main_login": "",
        }
        self.headers = {
            "User-Agent": self.ckey.userAgent,
            "Referer": "https://v.qq.com",
            "Cookie": self.ck,
        }
        self.re = requests.session()
        self.re.headers.update(self.headers)
        self.login()

    def login(self):
        cookie = dealck(self.ck)

        for logintoken_index in self.logintoken:
            self.logintoken[logintoken_index] = cookie.get(
                logintoken_index
            ) or cookie.get("vqq_" + logintoken_index)
            if not self.logintoken[logintoken_index]:
                raise ValueError(
                    "cookie无效,请重新获取cookie:"
                    " 'https://access.video.qq.com/user/auth_refresh'"
                )

        self.h38 = cookie.get("_qimei_h38", "")
        self.guid = cookie.get("video_guid", "")

        url = "https://access.video.qq.com/user/auth_refresh"
        params = {
            "vappid": "11059694",
            "vsecret": "fdf61a6be0aad57132bc5cdf78ac30145b6cd2c1470b0cfe",
            "type": "qq",
            "g_tk": "",
            "g_vstk": djb2Hash(self.logintoken.get("vusession", "")) or "",
            "g_actk": djb2Hash(self.logintoken.get("access_token", "")) or "",
            "_": str(int(time.time() * 1000)),
        }
        url_res = self.re.get(url, params=params)

        data_text = url_res.text
        if "=" in data_text:
            data_text_split = data_text.split("=")[1]
            data = json.loads(data_text_split)
        else:
            data = {}
        access_token = data.get("access_token", "")
        vusession = data.get("vusession", "")
        if access_token:
            self.ck = self.ck.replace(
                self.logintoken.get("access_token", ""), access_token
            )
        if vusession:
            self.ck = self.ck.replace(
                self.logintoken.get("vusession", ""), vusession
            )
        ck = self.ck.replace("vqq_", "")
        self.logintoken["access_token"] = access_token
        self.logintoken["vusession"] = vusession
        self.headers = {
            "User-Agent": self.ckey.userAgent,
            "Referer": "https://v.qq.com",
            "Cookie": ck,
        }
        self.re.headers.update(self.headers)

        cookie_config.write_cookie(WebEnum.tx, self.ck)

    def dec_res(self, data: str, c=1):
        data_json_de = json.loads(b64decode(data))
        rc = b64decode(data_json_de["rc"])
        aanc = b64decode(data_json_de["aanc"])
        anc = b64decode(data_json_de["anc"])
        key, iv = eval(rsa_dec(self.key, rc))["algo_params"]
        algo_list = eval(
            aes_decrypt(key.encode(), aanc, iv.encode()).decode()
        )["algo_list"]
        key, iv = algo_list[0]["algo_params"]
        if c == 1:
            data_json_en = json.loads(
                aes_decrypt(key.encode(), anc, iv.encode()).decode()
            )
        else:
            data_json_en = base64.b64encode(
                aes_decrypt(key.encode(), anc, iv.encode())
            ).decode()
        return data_json_en

    def get(
        self,
        vid=None,
        url="https://v.qq.com/x/cover/mzc002007qle9m2/x0047r3k6wy.html",
        defn="hdr10",
    ):
        vid = url.split("/")[-1].split(".")[0] if vid is None else vid
        tm = int(time.time())
        ckey = self.ckey.ckey92(
            tm=tm, vid=vid, guid=self.guid, h38=self.h38, url=url
        )
        params = {
            "vid": vid,
            "defn": defn,
            "ehost": url,
            "refer": url,
            "guid": self.guid,
            "cKey": ckey,
            "logintoken": json.dumps(self.logintoken, separators=(",", ":")),
            "tm": tm,
            "charge": "0",
            "otype": "ojson",
            "spau": "1",
            "spwm": "1",
            "sphls": "2",
            "host": "v.qq.com",
            "sphttps": "1",
            "encryptVer": "9.2",
            "clip": "4",
            "flowid": "",
            "sdtfrom": "v1010",
            "appVer": "1.28.2",
            "unid": "",
            "auth_from": "",
            "auth_ext": "",
            "fhdswitch": "0",
            "spsrt": "2",
            "lang_code": "0",
            "spvvpay": "1",
            "spadseg": "3",
            "spm3u8tag": "67",
            "spmasterm3u8": "3",
            "drm": "40",
            "platform": "10201",
            "dtype": 3,
            "spav1": 15,
            "hevclv": 28,
            "spsfrhdr": 100,
            "spvideo": 1044,
            "spaudio": 70,
            "defnpayver": 7,
        }
        response = self.re.get(
            "https://h5vv6.video.qq.com/getinfo", params=params
        )
        data = response.json()
        if "anc" in data:
            anc = data["anc"]
            data = self.dec_res(anc)
        return data

    @staticmethod
    def get_list(url):
        def get_video_data(data, ret=[]):
            cookies = {
                "appid": "wxa75efa648b60994b",
                "vversion_name": "8.2.95.1",
                "video_bucketid": "4",
                "video_omgid": "",
            }
            params = {
                "video_appid": "3000002",
                "guid": "",
                "vplatform": "5",
                "callerid": "3000002",
            }
            headers = {
                "Accept-Encoding": "gzip,compress,br,deflate",
                "Connection": "keep-alive",
                "Host": "pbaccess.video.qq.com",
                "Referer": "https://servicewechat.com/wxa75efa648b60994b/629/page-frame.html",  # noqa: E501
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X)"
                    " AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
                    " MicroMessenger/8.0.42(0x18002a2e) NetType/WIFI"
                    " Language/zh_CN"
                ),
                "content-type": "application/json",
            }
            url = "https://pbaccess.video.qq.com/trpc.universal_backend_service.page_server_rpc.PageServer/GetPageData"  # noqa: E501
            response = requests.post(
                url, headers=headers, cookies=cookies, params=params, data=data
            )
            response_data = response.json()
            module_list_datas = response_data["data"]["module_list_datas"]
            for module_list_data in module_list_datas:
                module_data = module_list_data["module_datas"][0]
                if (
                    module_data["module_params"]["module_type"]
                    == "episode_list"
                ):
                    has_next = module_data["module_params"]["has_next"]
                    item_datas = module_data["item_data_lists"]["item_datas"]
                    for item_data in item_datas:
                        item_type = item_data["item_type"]
                        if int(item_type) == 23:
                            log.info(item_data["item_params"]["sub_title"])
                            continue
                        item_params = item_data["item_params"]
                        play_type = item_params["play_type"]
                        if int(play_type) != 1:
                            continue
                        cover_c_title = item_params["cover_c_title"]
                        play_title = item_params["play_title"]
                        vid = item_params["vid"]
                        ret.append([cover_c_title, play_title, vid])
                    if has_next == "true":
                        next_page_context = module_data["module_params"][
                            "next_page_context"
                        ]
                        data = {
                            "page_params": {
                                "page_type": "detail_operation",
                                "cid": "",
                                "page_id": "vsite_episode_list",
                                "page_context": next_page_context,
                            }
                        }
                        get_video_data(
                            json.dumps(data, separators=(",", ":")), ret
                        )
                    else:
                        break
            return ret

        cid = url.split("/")[5].split(".")[0]
        data = {"page_params": {"page_type": "video_detail", "cid": cid}}

        data = get_video_data(json.dumps(data, separators=(",", ":")))
        return data

    def start(self, url):
        self.run(url)

    def run(self, url):
        list = self.get_list(url)
        log.info(
            tabulate(
                list,
                headers=["cover_c_title", "play_title", "vid"],
                tablefmt="grid",
                showindex=range(1, len(list) + 1),
            )
        )

        av_index_input = typer.prompt(select_prompt)
        log.debug(f"下载视频序号文件: {av_index_input}")

        # -表示范围，,表示多个，如1-3表示1,2,3
        if "-" in av_index_input:
            start, end = av_index_input.split("-")
            av_index_list = list(range(int(start), int(end) + 1))
        else:
            # ,表示多个，如1,3,5,7
            av_index_list = av_index_input.split(",")

        for av_index in av_index_list:
            viddeodata = list[int(av_index) - 1]
            c_title, title, vid = viddeodata
            data = self.get(vid=vid, url=url)
            fi = data.get("fl", {}).get("fi", {})
            if not fi:
                log.info("无法获取清晰度,跳过")
                continue

            defn = []
            for f in fi:
                cname = f["cname"]
                name = f["name"]
                fs = f["fs"]
                size = get_size(fs)
                fn = f["id"]
                defn.append([fn, name, cname, size, fs])
            defn.sort(key=lambda x: x[-1], reverse=True)
            log.info(
                tabulate(
                    defn,
                    headers=["id", "fn", "cname", "size", "rsize"],
                    tablefmt="pretty",
                    showindex=range(1, len(defn) + 1),
                )
            )

            v_index_input = typer.prompt(select_prompt)
            log.debug(f"下载视频序号文件: {v_index_input}")

            # -表示范围，,表示多个，如1-3表示1,2,3
            if "-" in v_index_input:
                start, end = v_index_input.split("-")
                v_index_list = list(range(int(start), int(end) + 1))
            else:
                # ,表示多个，如1,3,5,7
                v_index_list = v_index_input.split(",")

            for v_index in v_index_list:
                defn_fn = defn[int(v_index) - 1][1]
                defn_size = defn[int(v_index) - 1][3]

                rr = (
                    self.get(vid, url, defn_fn) if defn_fn != "hdr10" else data
                )
                vi = rr["vl"]["vi"][0]
                ui = vi["ul"]["ui"]
                enc = vi.get("enc")
                if enc == "1":
                    if "ckc" in vi:
                        # lic_url = vi["ckc"]
                        m3u8 = rr["play"]["audiolist"][0]["m3u8"]
                        pssh = m3u8.split("base64,")[1].split('",')[0]
                        log.info(pssh)
                        log.info("不支持wv")
                    elif "base" in vi:
                        # tm = data["tm"]
                        # base = vi["base"]
                        # linkvid = vi["lnk"]
                        # appVer = "1.28.2"
                        # platform = 10201
                        log.info("不支持chacha20")

                    continue

                m3u8url: str = ""
                for a in ui:
                    m3u8url = a["url"]
                    m3u8url = (
                        m3u8url
                        if not m3u8url.endswith("/")
                        else m3u8url + a["hls"]["pt"]
                    )
                    break

                if not m3u8url:
                    log.info("无法获取m3u8url,跳过")
                    continue

                # savepath = f"./download/tx/{c_title}/"
                save_name = (f"{title}_{defn_fn}_{defn_size}").replace(
                    " ", "_"
                )
                log.debug(f"save_name:::{save_name}")

                tx_sh_file_path = tx_sh_dir_path / f"{save_name}.sh"

                save_dir_path = tx_save_path / (f"{c_title}").replace(" ", "_")

                tx_cache_path.mkdir(parents=True, exist_ok=True)
                tx_history_path.mkdir(parents=True, exist_ok=True)
                save_dir_path.mkdir(parents=True, exist_ok=True)

                tx_sh_dir_path.mkdir(parents=True, exist_ok=True)

                cmd_parts = [
                    str(m3u8_bin_path),
                    m3u8url,
                    f"--tmp-dir {tx_cache_path}",
                    f"--save-name {save_name}",
                    f"--save-dir {save_dir_path}",
                    "--thread-count 16",
                    "--download-retry-count 30",
                    "--auto-select",
                    "--check-segments-count",
                ]
                cmd = " ".join(cmd_parts)

                cmd_content = f"#!/usr/bin/env bash\n{cmd}"
                log.debug(f"cmd_content::: {cmd_content}")

                with open(tx_sh_file_path, "a", encoding="utf-8") as f:
                    f.write(cmd_content)
                    f.write("\n")
                log.info(f"链接文件已生成: {tx_sh_file_path}")
                log.info(
                    "查看sh目录下的链接文件文件: media-web-dl show tx-save-sh"
                )
                log.info(
                    "下载sh目录下链接文件的视频: media-web-dl dl"
                    " tx-save-sh-video"
                )
