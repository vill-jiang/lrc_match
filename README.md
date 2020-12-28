# lrc_match
Auto match .lrc lyrics for music file. KuGou > QQ > Netease.

自动为音乐文件下载 .lrc 歌词. 优先级: 酷狗音乐 > QQ 音乐 > 网易云音乐.

```shell
NAME
    lrc_match.py

SYNOPSIS
    lrc_match.py <flags>

FLAGS
    --music_dir=MUSIC_DIR    # str 音乐文件夹，默认为当前目录
    --music_file=MUSIC_FILE  # str 指定某个音乐文件
    --force=FORCE            # bool 强制覆盖已有lrc歌词文件
    --only_search            # bool 仅搜索, 不保存lrc歌词文件
```

网易云音乐使用 API: http://www.hjmin.com

Root 项目: https://github.com/yedanten/DownloadLrcFromNKQ
