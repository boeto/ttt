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
        url = input("请输入视频链接：")
        # if "iqiyi.com" in url:
        #     iq.run(url)
        if "youku.com" in url:
            youku.start(url)
        else:
            print("暂不支持该链接")
