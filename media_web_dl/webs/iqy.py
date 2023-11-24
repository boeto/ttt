import base64
import json
import time
from typing import Any, Dict, List
from urllib import parse
import requests
from tabulate import tabulate
import typer
from media_web_dl.pywidevine.L3.cdm import deviceconfig
from media_web_dl.pywidevine.L3.decrypt.wvdecryptcustom import WvDecrypt
from media_web_dl.utils.tools import dealck, md5, get_size, get_pssh

from media_web_dl.utils.paths import output_path
from media_web_dl.utils.logger import log
from media_web_dl.webs.common import m3u8_bin_path

# paths
iqy_output_path = output_path / "iqy"

iqy_cache_path = iqy_output_path / "cache"
iqy_save_path = iqy_output_path / "save"
iqy_url_file_path = iqy_output_path / "url_file"
iqy_history_path = iqy_output_path / "history"

iqy_sh_dir_path = iqy_url_file_path / "sh"
iqy_txt_dir_path = iqy_url_file_path / "txt"
iqy_m3u8_dir_path = iqy_url_file_path / "m3u8"


def get_key(pssh):
    LicenseUrl = "https://drml.video.iqiyi.com/drm/widevine?ve=0"
    wvdecrypt = WvDecrypt(
        init_data_b64=pssh,
        cert_data_b64="",
        device=deviceconfig.device_android_generic,
    )
    widevine_license = requests.post(
        url=LicenseUrl, data=wvdecrypt.get_challenge()
    )
    license_b64 = base64.b64encode(widevine_license.content)
    wvdecrypt.update_license(license_b64)
    correct, keys = wvdecrypt.start_process()
    for key in keys:
        log.info("--key " + key)
    key_string = " ".join([f"--key {key}" for key in keys])
    return key_string


class Iqy:
    def __init__(self, aqy):
        self.ck = aqy
        ckjson = dealck(aqy)
        self.P00003 = ckjson.get("P00003", "1008611")
        self.pck = ckjson.get("P00001")
        self.dfp = ckjson.get("__dfp", "").split("@")[0]
        self.QC005 = ckjson.get("QC005", "")
        self.requests = requests.Session()

        self.requests.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0"
                    " Safari/537.36"
                ),
                "Cookie": self.ck,
            }
        )
        self.bop = f'{{"version":"10.0","dfp":"{self.dfp}","b_ft1":8}}'

    @staticmethod
    def parse(shareurl):
        try:
            url = "https://iface2.iqiyi.com/video/3.0/v_play"
            params = {
                "app_k": "20168006319fc9e201facfbd7c2278b7",
                "app_v": "8.9.5",
                "platform_id": "10",
                "dev_os": "8.0.1",
                "dev_ua": "Android",
                "net_sts": "1",
                "secure_p": "GPhone",
                "secure_v": "1",
                "dev_hw": '{"cpu":0,"gpu":"","mem":""}',
                "app_t": "0",
                "h5_url": shareurl,
            }
            response = requests.get(url, params=params)
            data = response.json()

            pid = data["play_pid"]
            aid = data["play_aid"]
            tvid = data["play_tvid"]
            Album = data["album"]
            Title = Album["_t"]
            Cid = Album["_cid"]
            return pid, aid, tvid, Title, Cid
        except Exception as e:
            log.info(f"parse shareurl失败: {e}")
            return None, None, None, None, None

    @staticmethod
    def get_avlistinfo(title, albumId, cid, pid):
        rets = []
        page = 1
        size = 200

        def getlist6():
            url = "https://pcw-api.iqiyi.com/album/source/svlistinfo"
            params = {
                "cid": "6",
                "sourceid": pid,
                "timelist": ",".join([str(i) for i in range(2000, 2026)]),
            }
            response = requests.get(url, params=params)
            data = response.json()["data"]

            for a, b in data.items():
                for i in b:
                    ret = {
                        "album": title,
                        "name": i["name"],
                        "tvId": i["tvId"],
                    }
                    rets.append(ret)

        def getlist():
            aid = albumId
            url = "https://pcw-api.iqiyi.com/albums/album/avlistinfo"
            params = {"aid": aid, "page": page, "size": size}
            response = requests.get(url, params=params).json()
            if response["code"] != "A00000":
                return None
            data = response["data"]
            total = data["total"]
            epsodelist: List[Dict[str, Any]] = data["epsodelist"]

            if total > size:
                for i in range(2, total // size + 2):
                    params["page"] = i
                    response = requests.get(url, params=params).json()
                    epsodelist.extend(response["data"]["epsodelist"])
            for epsode in epsodelist:
                ret = {
                    "album": title,
                    "name": epsode["name"],
                    "tvId": epsode["tvId"],
                }
                rets.append(ret)

        if cid == 1:
            ret = {
                "album": title,
                "name": title,
                "tvId": albumId,
            }
            rets.append(ret)
        elif cid == 6:
            getlist6()
        else:
            getlist()
        return rets

    def get_param(self, tvid="", vid=""):
        tm = str(int(time.time() * 1000))
        authKey = md5("d41d8cd98f00b204e9800998ecf8427e" + tm + str(tvid))
        params = {
            "tvid": tvid,
            "bid": "600",
            "vid": "",
            "src": "01010031010000000000",
            "vt": "0",
            "rs": "1",
            "uid": self.P00003,
            "ori": "pcw",
            "ps": "0",
            "k_uid": self.QC005,
            "pt": "0",
            "d": "0",
            "s": "",
            "lid": "0",
            "cf": "0",
            "ct": "0",
            "authKey": authKey,
            "k_tag": "1",
            "dfp": self.dfp,
            "locale": "zh_cn",
            "pck": self.pck,
            "k_err_retries": "0",
            "up": "",
            "sr": "1",
            "qd_v": "5",
            "tm": tm,
            "qdy": "u",
            "qds": "0",
            "ppt": "0",
            "k_ft1": "706436220846084",
            "k_ft4": "1162321298202628",
            "k_ft2": "262335",
            "k_ft5": "134217729",
            "k_ft6": "128",
            "k_ft7": "688390148",
            "fr_300": "120_120_120_120_120_120",
            "fr_500": "120_120_120_120_120_120",
            "fr_600": "120_120_120_120_120_120",
            "fr_800": "120_120_120_120_120_120",
            "fr_1020": "120_120_120_120_120_120",
        }
        dash = "/dash?"
        for a, b in params.items():
            dash += f"{a}={b}&"
        dash = dash[:-1] + "&bop=" + parse.quote(self.bop) + "&ut=14"
        vf = md5(dash + "tle8orw4vetejc62int3uewiniecr18i")
        dash += f"&vf={vf}"
        return dash

    def get_dash(self, tvid="", vid=""):
        params = self.get_param(tvid=tvid, vid=vid)
        url = "https://cache.video.iqiyi.com" + params
        res = self.requests.get(url)
        return res.json()

    def run(self, url):
        pid, aid, tvid, title, cid = self.parse(url)
        if pid is None:
            log.error("解析失败")
            return
        avlist = self.get_avlistinfo(title, aid, cid, pid)
        if avlist is None:
            log.error("获取列表失败")
            return
        table = tabulate(
            avlist,
            headers="keys",
            tablefmt="pretty",
            showindex=range(1, len(avlist) + 1),
        )
        log.info(table)
        av_index_input = typer.prompt("""
#输入格式
单集: 下载单个url文件, 例如: 5
范围: 下载范围内的url文件, 例如: 1-5
多个: 下载多个url文件, 例如: 1,3,5,7
请输入要下载的视频序号""")
        log.debug(f"下载视频序号文件: {av_index_input}")

        # -表示范围，,表示多个，如1-3表示1,2,3
        if "-" in av_index_input:
            start, end = av_index_input.split("-")
            av_index_list = list(range(int(start), int(end) + 1))
        else:
            # ,表示多个，如1,3,5,7
            av_index_list = av_index_input.split(",")

        for av_index in av_index_list:
            av_index = int(av_index)
            list_len = len(avlist)
            if av_index > list_len:
                log.error("序号大于列表数,请重新输入")
                break

            tvId = avlist[av_index - 1]["tvId"]
            avlist_name = avlist[av_index - 1]["name"]
            ctitle = avlist[av_index - 1]["album"]
            log.info(f"正在获取{ctitle} {avlist_name}的m3u8")
            response = self.get_dash(tvid=tvId)

            try:
                if response["data"]["boss_ts"]["code"] != "A00000":
                    log.error("获取m3u8失败\n")
                    log.error(response["data"]["boss_ts"]["msg"])
                    continue
            except Exception:
                pass
                # log.error(f"获取m3u8失败\n{e}")
            data = response["data"]
            program = data["program"]
            if "video" not in program:
                log.info("无视频")
                continue
            video_list = program["video"]
            # audio = program["audio"]
            # stl = program.get("stl", [])

            m3u8_list = []
            for video in video_list:
                #
                m3u8_data = video.get("m3u8", "")
                if not m3u8_data:
                    log.debug("该视频无m3u8文件,跳过下载")
                    continue
                scrsz = video.get("scrsz", "")
                vsize = get_size(video.get("vsize", ""))
                fr = str(video.get("fr", ""))

                m3u8_list.append((avlist_name, scrsz, vsize, fr, m3u8_data))
            tab_video_list = [
                (avlist_name, scrsz, vsize, fr)
                for avlist_name, scrsz, vsize, fr, m3u8_data in m3u8_list
            ]

            tab_video = tabulate(
                tab_video_list,
                headers=["name", "scrsz", "vsize", "fr"],
                tablefmt="pretty",
            )
            log.info(f"\n{tab_video}")

            for m3u8_list_index, (
                avlist_name,
                scrsz,
                vsize,
                fr,
                m3u8_data,
            ) in enumerate(m3u8_list):
                try:
                    # 视频文件名
                    save_name = (
                        f"{avlist_name}_{scrsz}_{vsize}_{fr}_{m3u8_list_index}"
                    ).replace(" ", "_")

                    # url-file保存路径
                    iqy_dot_m3u8_file_path = (
                        iqy_m3u8_dir_path / f"{save_name}.m3u8"
                    )
                    iqy_sh_file_path = iqy_sh_dir_path / f"{save_name}.sh"

                    # 以ctitle为文件夹名保存下载的视频文件
                    save_dir_path = iqy_save_path / f"{ctitle}"

                    iqy_cache_path.mkdir(parents=True, exist_ok=True)
                    iqy_history_path.mkdir(parents=True, exist_ok=True)
                    save_dir_path.mkdir(parents=True, exist_ok=True)

                    iqy_sh_dir_path.mkdir(parents=True, exist_ok=True)
                    iqy_m3u8_dir_path.mkdir(parents=True, exist_ok=True)

                    with open(
                        iqy_dot_m3u8_file_path, "w", encoding="utf-8"
                    ) as f:
                        f.write(m3u8_data)
                    log.info(f"m3u8文件已生成: {iqy_dot_m3u8_file_path}")

                    if m3u8_data.startswith('{"payload"'):
                        m3u8_data = json.loads(m3u8_data)
                        init = m3u8_data["payload"]["wm_a"]["audio_track1"][
                            "codec_init"
                        ]
                        pssh = get_pssh(init)
                        key_string = get_key(pssh)

                        cmd_parts = [
                            str(m3u8_bin_path),
                            str(iqy_dot_m3u8_file_path),
                            f"--tmp-dir {iqy_cache_path}",
                            f"--save-name {save_name}",
                            f"--save-dir {save_dir_path}",
                            "--thread-count 16",
                            "--download-retry-count 30",
                            "--auto-select",
                            "--check-segments-count",
                            key_string,
                            "-M format=mp4",
                        ]
                        cmd = " ".join(cmd_parts)
                    else:
                        cmd_parts = [
                            str(m3u8_bin_path),
                            str(iqy_dot_m3u8_file_path),
                            f"--tmp-dir {iqy_cache_path}",
                            f'--save-name "{save_name}"',
                            f'--save-dir "{save_dir_path}"',
                            "--thread-count 16",
                            "--download-retry-count 30",
                            "--auto-select",
                            "--check-segments-count",
                        ]
                        cmd = " ".join(cmd_parts)

                    cmd_content = f"#!/usr/bin/env bash\n#{cmd}\n{cmd}"
                    log.debug(f"cmd_content::: {cmd_content}")
                    with open(iqy_sh_file_path, "a", encoding="utf-8") as f:
                        f.write(cmd_content)
                        f.write("\n")
                    log.info(f"链接文件已生成: {iqy_sh_file_path}")
                    log.info(
                        "查看sh目录下的链接文件文件: media-web-dl show"
                        " iqy-save-sh"
                    )
                    log.info(
                        "下载sh目录下链接文件的视频: media-web-dl dl"
                        " iqy-save-sh-video"
                    )
                except Exception as e:
                    log.error(f"处理url-file文件失败: {e}")
                    continue

    def start(self, url):
        self.run(url)
