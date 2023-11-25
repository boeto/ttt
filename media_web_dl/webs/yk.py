import os
import re
from typing import Any, Dict
from requests import Session
import time
import json
from hashlib import md5
from urllib.parse import parse_qsl, urlsplit
import base64
from Crypto.Cipher import AES
from tabulate import tabulate
import typer

from media_web_dl.pywidevine.L3.cdm import deviceconfig
from media_web_dl.pywidevine.L3.decrypt.wvdecryptcustom import WvDecrypt
from media_web_dl.utils.logger import log

from media_web_dl.utils.tools import dealck
from media_web_dl.utils.paths import output_path
from media_web_dl.webs.common import m3u8_bin_path, select_prompt

session = Session()

# paths
yk_output_path = output_path / "yk"

yk_cache_path = yk_output_path / "cache"
yk_save_path = yk_output_path / "save"
yk_url_file_path = yk_output_path / "url_file"
yk_history_path = yk_output_path / "history"

yk_sh_dir_path = yk_url_file_path / "sh"
yk_txt_dir_path = yk_url_file_path / "txt"
yk_m3u8_dir_path = yk_url_file_path / "m3u8"


class YouKu:
    def __init__(self, cookie):
        self.cookie = dealck(cookie)
        self.r = "xWrtQpP4Z4RsrRCY"
        self.R = "aq1mVooivzaolmJY5NrQ3A=="
        self.key = ""
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
            ),
        }
        session.headers.update(self.headers)
        session.cookies.update(self.cookie)
        self.ptoken = self.cookie.get("P_pck_rm")
        self.utida = "ZIH81OVlRSMDAOQQiG52i4cO"

    def youku_sign(self, t, data, token):
        appKey = "24679788"  # 固定值
        """token值在cookie中"""
        sign = token + "&" + t + "&" + appKey + "&" + data
        md = md5()
        md.update(sign.encode("UTF-8"))
        sign = md.hexdigest()
        return sign

    def utid(self):
        json_cookie = session.cookies.get_dict()
        session.cookies.clear()
        session.cookies.update(json_cookie)
        utid = json_cookie.get("cna")
        token = json_cookie.get("_m_h5_tk").split("_")[0]
        return {"utid": utid, "token": token}

    # 若直接在首页小窗口上复制的视频网址，是重定向的网址。
    def redirect(self, url):
        # headers = {
        #     "referer": "https://www.youku.com/",
        #     "user-agent": (
        #         "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36"
        #         " (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        #     ),
        # }
        resp = session.get(url=url)
        return resp.url

    def page_parser(self, url):
        vid = re.findall(r"id_(.*?)\.html", url)[0]
        url = "https://openapi.youku.com/v2/videos/show.json"
        params = {
            "client_id": "53e6cc67237fc59a",
            "package": "com.huawei.hwvplayer.youku",
            "ext": "show",
            "video_id": vid,
        }
        try:
            response = session.get(url, params=params).json()
            showid = response["show"]["id"]
            return {"current_showid": showid, "videoId": 0, "vid": vid}
        except Exception as e:
            log.error(f"获取showid失败:{e}")
            raise e

    def get_emb(self, videoId):
        emb = base64.b64encode(
            ("%swww.youku.com/" % videoId).encode("utf-8")
        ).decode("utf-8")
        return emb

    # 这个函数用来获取元素的第一个值
    def takeOne(self, elem):
        return float(elem[0])

    def m3u8_url(self, t, params_data, sign, vid):
        url = "https://acs.youku.com/h5/mtop.youku.play.ups.appinfo.get/1.1/"

        params = {
            "jsv": "2.5.8",
            "appKey": "24679788",
            "t": t,
            "sign": sign,
            "api": "mtop.youku.play.ups.appinfo.get",
            "v": "1.1",
            "timeout": "20000",
            "YKPid": "20160317PLF000211",
            "YKLoginRequest": "true",
            "AntiFlood": "true",
            "AntiCreep": "true",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp1",
            "data": params_data,
        }
        resp = session.get(url=url, params=params)
        result = resp.text
        # log.info(result)
        data = json.loads(result[12:-1])
        # log.info(data)
        ret = data["ret"]
        video_lists = []

        if ret == ["SUCCESS::调用成功"]:
            stream = data.get("data", {}).get("data", {}).get("stream")
            if not stream:
                log.info("无法获取视频流")
                return
            title = data["data"]["data"]["video"]["title"]
            log.info("解析成功")
            keys: Dict[str, Any] = {}
            tv_stream = self.get_TV_stream(vid)
            stream.extend(tv_stream)
            for video in stream:
                m3u8_url = video["m3u8_url"]
                width = video["width"]
                height = video["height"]
                size = video.get("size", 0)
                size = "{:.1f}".format(float(size) / 1048576)
                drm_type = video["drm_type"]
                audio_lang = video["audio_lang"]
                if video["drm_type"] == "default":
                    key = ""
                elif audio_lang not in keys.keys():
                    if drm_type == "cbcs":
                        license_url = video["stream_ext"]["uri"]
                        key = self.get_cbcs_key(license_url, m3u8_url)
                        if key[0]:
                            key = key[1][0]
                    else:
                        encryptR_server = video["encryptR_server"]
                        copyright_key = video["stream_ext"]["copyright_key"]
                        key = self.copyrightDRM(
                            self.r, encryptR_server, copyright_key
                        )
                    keys[audio_lang] = key
                else:
                    key = keys[audio_lang]
                video_lists.append(
                    [
                        title,
                        size + "M",
                        f"{width}x{height}",
                        drm_type,
                        key,
                        video["stream_type"],
                        m3u8_url,
                        video.get("size", 0),
                    ]
                )
            video_lists = sorted(
                video_lists, key=lambda x: x[-1], reverse=True
            )
            tb = tabulate(
                [[*video_lists[i][:6]] for i in range(len(video_lists))],
                headers=[
                    "标题",
                    "分辨率",
                    "视频大小",
                    "drm_type",
                    "base64key",
                    "stream_type",
                ],
                tablefmt="pretty",
                showindex=range(1, len(video_lists) + 1),
            )

            log.info(tb)
            ch_input = typer.prompt(f"{select_prompt}")
            log.debug(f"下载视频序号文件: {ch_input}")

            # -表示范围，,表示多个，如1-3表示1,2,3
            if "-" in ch_input:
                start, end = ch_input.split("-")
                ch = list(range(int(start), int(end) + 1))
            else:
                # ,表示多个，如1,3,5,7
                ch = ch_input.split(",")

            for i in ch:
                i = int(i)
                if i > len(video_lists):
                    log.error("序号大于列表数,请重新输入")
                    break

                (
                    title,
                    size,
                    resolution,
                    drm_type,
                    key,
                    stream_type,
                    m3u8_url,
                    _,
                ) = video_lists[i - 1]

                # m3u8_info = (
                #     f"title:{title}, size:{size}, resolution:{resolution},"
                #     f" drm_type:{drm_type}, key:{key},"
                #     f" stream_type:{stream_type}"
                # )

                save_name = (
                    f"{title}_{resolution}_{drm_type}_{stream_type}_{size}_{i}"
                ).replace(" ", "_")
                log.debug(f"save_name:::{save_name}")

                yk_sh_file_path = yk_sh_dir_path / f"{save_name}.sh"
                yk_txt_file_path = yk_txt_dir_path / f"{save_name}.txt"
                yk_dot_m3u8_file_path = yk_m3u8_dir_path / f"{save_name}.m3u8"

                save_dir_path = yk_save_path / (f"{title}").replace(" ", "_")

                yk_cache_path.mkdir(parents=True, exist_ok=True)
                yk_history_path.mkdir(parents=True, exist_ok=True)
                save_dir_path.mkdir(parents=True, exist_ok=True)

                yk_sh_dir_path.mkdir(parents=True, exist_ok=True)
                yk_txt_dir_path.mkdir(parents=True, exist_ok=True)
                yk_m3u8_dir_path.mkdir(parents=True, exist_ok=True)

                # rm3u8_url = m3u8_url.replace("%", "%%")
                if m3u8_url.startswith("http"):
                    common_args = (
                        f'{m3u8_bin_path} "{m3u8_url}" --tmp-dir'
                        f' {yk_cache_path} --save-name "{save_name}"'
                        f' --save-dir "{save_dir_path}" --thread-count 16'
                        " --download-retry-count 30 --auto-select"
                        " --check-segments-count"
                    )
                    if drm_type == "default":
                        cmd = common_args
                    elif drm_type == "cbcs":
                        cmd = f"{common_args} --key {key}  -M format=mp4"
                    else:
                        txt = f"""
                    #OUT,{save_dir_path}
                    #DECMETHOD,ECB
                    #KEY,{key}
                    {title}_{resolution}_{size},{m3u8_url}"""
                        if yk_txt_file_path.exists():
                            log.debug(f"txt:{txt}")
                            log.info(
                                f"{yk_txt_file_path}文件已存在,如需要重新下载,请删除该文件"
                            )
                            continue
                        with open(
                            yk_txt_file_path, "a", encoding="utf-8"
                        ) as f:
                            f.write(txt)
                        log.info(f"{yk_txt_file_path}文件已经写入: {txt}")
                        continue

                else:
                    uri = re.findall(r'URI="(.*)"', m3u8_url)[0]
                    m3u8_text = session.get(uri).text
                    keyid = re.findall(r"KEYID=0x(.*),IV", m3u8_text)[0]

                    if yk_dot_m3u8_file_path.exists():
                        log.debug(f"m3u8_url:{m3u8_url}")
                        log.info(
                            f"{yk_dot_m3u8_file_path}文件已存在,如需要重新下载,请删除该文件"
                        )
                        continue
                    with open(
                        yk_dot_m3u8_file_path, "w", encoding="utf-8"
                    ) as f:
                        f.write(m3u8_url)
                    log.info(f"{yk_dot_m3u8_file_path}文件已写入: {m3u8_url}")

                    key = "{}:{}".format(keyid, base64.b64decode(key).hex())
                    common_args = (
                        f'{m3u8_bin_path} "{yk_dot_m3u8_file_path}"'
                        f" --tmp-dir {yk_cache_path} --save-name"
                        f' "{save_name}" --save-dir "{save_dir_path}"'
                        " --thread-count 16 --download-retry-count 30"
                        " --auto-select --check-segments-count"
                    )
                    cmd = f"{common_args} --key {key} -M format=mp4"

                cmd_content = f"#!/usr/bin/env bash\n{cmd}"

                if yk_sh_file_path.exists():
                    log.debug(f"cmd_content:{cmd_content}")
                    log.info(
                        f"{yk_sh_file_path}文件已存在,如需要重新下载,请删除该文件"
                    )
                    continue
                with open(yk_sh_file_path, "a", encoding="utf-8") as f:
                    f.write(cmd_content)
                    f.write("\n")
                os.chmod(yk_sh_file_path, 0o755)
                log.info(f"{yk_sh_file_path}文件已写入: {cmd_content}")

                log.info(f"链接文件已生成: {yk_sh_file_path}")
                log.info(
                    "查看sh目录下的链接文件文件: media-web-dl show yk-save-sh"
                )
                log.info(
                    "下载sh目录下链接文件的视频: media-web-dl dl"
                    " yk-save-sh-video"
                )
        elif ret == ["FAIL_SYS_ILLEGAL_ACCESS::非法请求"]:
            log.info("请求参数错误")
        elif ret == ["FAIL_SYS_TOKEN_EXOIRED::令牌过期"]:
            log.info("Cookie过期")
            return 10086
        else:
            log.info(ret[0])
        return 0

    def copyrightDRM(self, r, encryptR_server, copyright_key):
        retry_count = 0
        while retry_count < 5:
            try:
                crypto_1 = AES.new(r.encode(), AES.MODE_ECB)
                key_2 = crypto_1.decrypt(base64.b64decode(encryptR_server))
                crypto_2 = AES.new(key_2, AES.MODE_ECB)

                # 对copyright_key进行base64解码
                decoded = base64.b64decode(copyright_key)

                # 对解码后的结果进行解密
                decrypted = crypto_2.decrypt(decoded)

                # 将b2转换为一个base64编码的字符串
                string_64 = base64.b64encode(decrypted)

                return string_64

            except Exception as e:
                log.error(f"解码错误: {e}")
                retry_count += 1
                time.sleep(3)
        raise Exception("解码重试次数超过限制")

    def get_cbcs_key(self, license_url, m3u8_url):
        headers = {
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                " Edg/114.0.1823.82"
            )
        }
        m3u8data = session.get(m3u8_url, headers=headers).text
        key_url = re.findall(r"URI=\"(.*?)\"", m3u8data)[0]
        response_text = session.get(key_url, headers=headers).text
        pssh = (
            response_text.split("data:text/plain;base64,").pop().split('",')[0]
        )
        wvdecrypt = WvDecrypt(
            init_data_b64=pssh,
            cert_data_b64="",
            device=deviceconfig.device_android_generic,
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                " Edg/114.0.1823.82"
            ),
        }
        dic = dict(parse_qsl(urlsplit(license_url).query))
        url = license_url.split("?")[0]
        dic["licenseRequest"] = base64.b64encode(
            wvdecrypt.get_challenge()
        ).decode()
        dic["drmType"] = "widevine"
        response = session.post(url, data=dic, headers=headers)
        license_b64 = response.json()["data"]
        wvdecrypt.update_license(license_b64)
        Correct, keyswvdecrypt = wvdecrypt.start_process()
        if Correct:
            return Correct, keyswvdecrypt

    def get_TV_stream(self, vid):
        headers = {"user-agent": "OTTSDK;1.0.8.6;Android;9;2203121C"}

        def getdata():
            response = session.get(url, headers=headers, params=params)
            try:
                data = response.json()["data"]
                title = data["show"]["title"]
                streams = data["stream"]
                streamss.extend(streams)
                return title, streams
            except Exception:
                return None, []

        url = "https://ups.youku.com/ups/get.json"  # light_get.json
        params = {
            "ckey": "7B19C0AB12633B22E7FE81271162026020570708D6CC189E4924503C49D243A0DE6CD84A766832C2C99898FC5ED31F3709BB3CDD82C96492E721BDD381735026",  # noqa
            "client_ip": "192.168.3.1",
            "client_ts": "1697343919",
            "utid": self.utida,
            "pid": "36281532078091",
            # HAIER_PID = "36214723575196";
            # JIMI_PID = "3b777e6ae3c99e26";
            # SONY_PID = "36281532078091";
            "player_type": "dnahard",  # system:hls,dnahard: cmfv
            "app_ver": "11.4.6.4",  # 2121104604,2121100600,11.0.6.0,11.4.6.4
            "ccode": (
                "0103010261"
            ),  # sony :0103010261, jimi:010301025C,haier:0103010275 280
            "player_source": "21",  # 20 sdr 21hfr 22dolby 23bit10
            "encryptR_client": "fTWuKHLOVUoOide+VH/h8w==",
            "key_index": "key01",
            "vid": vid,
            "h265": "1",
            "media_type": "standard,sei",
            "client_id": "",
            "ptoken": self.ptoken,
            "drm_type": "7",
            "extag": "EXT-X-PRIVINF",
            "extag_fields": "STREAMTYPE",
            "device_name": "XR-98X90L",
            "play_ability": "405929984",
            "preferClarity": "23",
            "master_m3u8": "0",
            "play_ability_v2": "2222222",
            "site": "1",
            "fu": "1",
            "vs": "1.0",
            "os": "android",
            "osv": "12.1.1",
            "bt": "tv",
            "aw": "a",
            "p": "27",
            "mdl": "XR-98X90L",
            "device_model": "XR-98X90L",
            "": "",
        }
        streamss: list[Any] = []
        player_source = [20, 23, 22, 21]
        player_type = ["system", "dnahard"]
        for i in player_source:
            params["player_source"] = str(i)
            for j in player_type:
                params["player_type"] = j
                getdata()
        params["ccode"] = "0103010275"
        params["player_source"] = "21"
        params["player_type"] = "dnahard"
        getdata()
        url = "https://ups.youku.com/ups/light_get.json"
        params["ccode"] = "0103010280"
        params["drm_type"] = 0
        getdata()
        streamss = sorted(streamss, key=lambda x: x["size"], reverse=True)
        return streamss

    def get(self, url):
        t = str(int(time.time() * 1000))
        user_info = self.utid()
        userid = user_info["utid"]
        page_info = self.page_parser(url)
        self.get_emb(page_info["videoId"])
        steal_params = {
            "ccode": "0502",
            "utid": userid,
            "version": "9.4.39",
            "ckey": "DIl58SLFxFNndSV1GFNnMQVYkx1PP5tKe1siZu/86PR1u/Wh1Ptd+WOZsHHWxysSfAOhNJpdVWsdVJNsfJ8Sxd8WKVvNfAS8aS8fAOzYARzPyPc3JvtnPHjTdKfESTdnuTW6ZPvk2pNDh4uFzotgdMEFkzQ5wZVXl2Pf1/Y6hLK0OnCNxBj3+nb0v72gZ6b0td+WOZsHHWxysSo/0y9D2K42SaB8Y/+aD2K42SaB8Y/+ahU+WOZsHcrxysooUeND",  # noqa
            "client_ip": "192.168.1.1",
            "client_ts": 1698373135,
        }
        biz_params = {
            "vid": page_info["vid"],
            "h265": 1,
            "preferClarity": 4,
            "media_type": "standard,subtitle",
            "app_ver": "9.4.39",
            "extag": "EXT-X-PRIVINF",
            "play_ability": 16782592,
            "master_m3u8": 1,
            "drm_type": 19,
            "key_index": "web01",
            "encryptR_client": self.R,
            "skh": 1,
            "last_clarity": 5,
            "clarity_chg_ts": 1689341442,
        }
        ad_params = {
            "vip": 1,
        }
        params_data = {
            "steal_params": json.dumps(steal_params),
            "biz_params": json.dumps(biz_params),
            "ad_params": json.dumps(ad_params),
        }
        params_data_dumps = json.dumps(params_data)
        sign = self.youku_sign(t, params_data_dumps, user_info["token"])
        return self.m3u8_url(t, params_data_dumps, sign, page_info["vid"])

    def start(self, url: str):
        url = self.redirect(url)
        for i in range(3):
            ret = self.get(url)
            if ret:
                continue
            break
