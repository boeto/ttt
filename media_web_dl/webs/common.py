m3u8_bin_path = "N_m3u8DL-RE"
select_prompt = """
#输入格式
单集: 下载单个url文件, 例如: 5
范围: 下载范围内的url文件, 例如: 1-5
多个: 下载多个url文件, 例如: 1,3,5,7
请输入要下载的视频序号"""


def get_input_int_list(input_index: str) -> list[int]:
    # -表示范围，,表示多个，如1-3表示1,2,3
    if "-" in input_index:
        start, end = input_index.split("-")
        int_list = list(range(int(start), int(end) + 1))
    else:
        # ,表示多个，如1,3,5,7
        int_list = [int(x) for x in input_index.split(",")]

    return int_list
