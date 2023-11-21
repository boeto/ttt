from tools import (
    check_file,
    get_config,
)

# from iqy import iqy
from yk import YouKu

if __name__ == "__main__":
    # check_file()
    config = get_config()

    yk = config["yk"]
    # aqy = config["aqy"]
    try:
        # iq = iqy(aqy)
        youku = YouKu(yk)
    except Exception as e:
        print("配置文件有误，请检查")
        print(e)
    while True:
        # url = input("请输入视频链接：")
        url = "https://v.youku.com/v_show/id_XNjEyNzIxMDQ5Mg==.html?s=fffe6088749e457d9d67&spm=a2hje.13141534.1_3.d_1_1&scm=20140719.apircmd.240015.video_XNjEyNzIxMDQ5Mg=="
        # if "iqiyi.com" in url:
        #     iq.run(url)
        if "youku.com" in url:
            youku.start(url)
        else:
            print("暂不支持该链接")
