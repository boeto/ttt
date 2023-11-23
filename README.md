# 基本说明

容器适配linux/amd64

## 使用 docker compose 安装
```bash
# 请先确保你挂载的文件夹是否存在和具有读写权限
# 如果是docker-compose命令的docker版本,
# 请对应修改docker compose为docker-compose

docker compose up -d
```

## media-web-dl cli使用说明
1. 以myuser用户身份启用容器bash
```bash
docker compose exec -u myuser media-web-dl /bin/bash
```

2. 下载url-file
```bash
media-web-dl dl url-file
-->输入视频链接: http://xxx.com/xxx/xxx/xxx
-->首次运行需要输入对应视频网站的cookie: 你的cookie
-->解析链接并输入需要下载的文件编号: 1-5
    #举例,输入下面说明的格式,建议使用范围格式生成多个url尝试下载视频,例如4k范围是1-5,则输入1-5
    单集: 下载单个url文件, 例如: 5
    范围: 下载范围内的url文件, 例如: 1-5
    多个: 下载多个url文件, 例如: 1,3,5,7
-->下载url-file完成
```

3. 通过url-file下载视频
```bash
# 下载yk视频
media-web-dl dl yk-save-sh-video
-->请输入要下载的视频编号: 3 #举例,输入单个数字编号下载对应编号的视频
-->视频下载中,注意留意日志是否报错,如果出现[ERROR]报错,则说明这个url-file是无效的,可以按下CTRL+C结束进程,不需要等待进程完成或重复尝试
-->处理过的url-file将移动到output/yk/history文件夹中,成功下载的视频文件在output/yk/save文件夹中
-->cache文件夹一般不需要理会,如果程序结束后还存在缓存文件,则可以手动清理cache下的所有文件
```
只适配处理url_file中的sh文件夹下的url文件,txt和m3u8中的url文件如有兴趣请自行研究

4. 其他
`media-web-dl --help`

## 郑重声明

**本软件仅限研究web视频下载技术，所以开源了，软件本身并不重要，其中的部分参数如何逆向才重要**