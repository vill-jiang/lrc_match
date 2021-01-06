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

### 示例

```shell
> ls
Ace组合 - 青花引.mp3
Glee Cast - Hey Jude.mp3
lrc_match.py
richard clayderman - 水边的阿狄丽娜.mp3
伍佰 - 突然的自我.flac
胡歌 - 逍遥叹.mp3

> python.exe .\lrc_match.py
[Parallel(n_jobs=24)]: Using backend ThreadingBackend with 24 concurrent workers.
[Parallel(n_jobs=24)]: Done   5 out of   5 | elapsed:    0.9s finished
+-------------------------------------------+------+------+------------------------------------------+--------+
| 文件名                                    | 状态 |  源  | 匹配名                                   | 匹配度 |
+-------------------------------------------+------+------+------------------------------------------+--------+
| .\Ace组合 - 青花引.mp3                    | 下载 | 酷狗 | Ace组合 - 青花引                         |  100.0 |
| .\Glee Cast - Hey Jude.mp3                | 下载 | 酷狗 | Glee Cast - Hey Jude (Glee Cast Version) |   83.5 |
| .\richard clayderman - 水边的阿狄丽娜.mp3 | 下载 |  QQ  | Richard Clayderman - 水边的阿狄丽娜      |  100.0 |
| .\伍佰 - 突然的自我.flac                  | 下载 | 酷狗 | 伍佰 - 突然的自我 (Live)                 |   88.0 |
| .\胡歌 - 逍遥叹.mp3                       | 下载 | 酷狗 | 胡歌 - 逍遥叹                            |  100.0 |
+-------------------------------------------+------+------+------------------------------------------+--------+

> ls
Ace组合 - 青花引.lrc
Ace组合 - 青花引.mp3
Glee Cast - Hey Jude.lrc
Glee Cast - Hey Jude.mp3
lrc_match.py
richard clayderman - 水边的阿狄丽娜.lrc
richard clayderman - 水边的阿狄丽娜.mp3
伍佰 - 突然的自我.flac
伍佰 - 突然的自我.lrc
胡歌 - 逍遥叹.lrc
胡歌 - 逍遥叹.mp3
```

### 依赖项
requests==2.23.0    # http访问

OpenCC==1.1.1       # 简繁转换

fire==0.3.1         # 命令行参数

joblib==0.17.0      # 并发包

prettytable==2.0.0  # 表格输出

fuzzywuzzy==0.18.0  # 模糊匹配


网易云音乐使用 API: http://www.hjmin.com

Root 项目: https://github.com/yedanten/DownloadLrcFromNKQ
