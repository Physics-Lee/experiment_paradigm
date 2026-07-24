# 患者实验运行说明

这份说明供实验同事使用。目前主要运行两个范式：

1. 闭锁患者中文指令范式（默认使用 v4）；
2. 新闻放松朗读范式。

请始终从仓库根目录运行命令：

```powershell
cd D:\Public_Repositories\experiment_paradigm
conda activate experiment_paradigm
```

两个范式默认使用无边框桌面全屏，不主动切换系统分辨率。按 `Esc` 可以退出。
完成的 trial 会自动保存为 `timestamp/` 下的一对 CSV 和 JSON 文件。

## 实验一：闭锁患者中文指令范式（v4）

### 直接运行

```powershell
python scripts\run_sentence_audio_zh.py
```

默认输入已经设置为：

- 刺激：`stimuli/yan_jiangyi_v4.txt`
- 音频：`assets/sentence_audio/yan_jiangyi_v4_slow/manifest.json`
- 微软语音：`zh-CN-XiaoxiaoNeural`
- 生成语速：`-50%`
- 呈现方式：逐字进度条
- trial 顺序：每个 block 默认独立随机打乱
- trial 间休息：默认显示黑底灰色十字

v4 包含 5 个指令：

1. 我想睡觉
2. 上厕所
3. 手机
4. 疼
5. 渴

屏幕仍显示“睡觉”，但生成音频时会将单独的“觉”隐藏映射为“叫”，使它读成
`shuì jiào`。

### 一个 block 的定义

一个 block 是把 v4 中的 5 个指令各呈现一次。

- 默认 `--repetitions 1`：运行 1 个 block，共 5 个 trial。
- `--repetitions 3`：运行 3 个 block，共 15 个 trial。
- 默认在每个 block 开始前分别随机打乱一次。
- 加 `--no-shuffle` 后，每个 block 都按刺激文件顺序呈现。

例如运行 3 个 block（默认随机顺序和灰色十字）：

```powershell
python scripts\run_sentence_audio_zh.py `
  --repetitions 3
```

### 每个 block 内的 trial 流程

实验开始后，只有第一个 trial 前有一次随机 1.5–2.5 秒黑屏基线。之后每个
trial 按以下流程运行：

1. 屏幕上半部分显示白色指令文字，下半部分显示红色正方形。
2. 保持 0.4–0.6 秒。
3. 播放该指令的逐字微软语音；文字和红方块保持不变。
4. 音频结束后继续静默保持 1.5–2.0 秒。
5. 提示音、方块由红变绿、首字进度同时开始。
6. 每个汉字的进度条默认运行 3.0 秒。
7. 相邻汉字之间默认暂停 0.5 秒。
8. 最后一个汉字完成后保持最终画面 0.5 秒。
9. trial 间随机休息 5.0–6.0 秒。
10. 默认休息画面显示灰色十字；加入 `--no-rest-cross` 后改为纯黑屏。

闭锁范式会自动进入下一个 trial，不需要鼠标点击。按 `Esc` 或单击鼠标可以
提前退出。

常用调整：

```powershell
# 固定按刺激文件顺序，并将休息画面改为纯黑
python scripts\run_sentence_audio_zh.py --no-shuffle --no-rest-cross

# 每个汉字改为 2 秒
python scripts\run_sentence_audio_zh.py --progress-duration 2.0

# 关闭同步提示音
python scripts\run_sentence_audio_zh.py --no-cue-tone

# 使用独占全屏
python scripts\run_sentence_audio_zh.py --display-mode exclusive
```

## 实验二：新闻放松朗读范式

### 直接运行

```powershell
python scripts\run_relaxing_news.py
```

默认输入：

- 新闻：`stimuli/news/2026_07_23.md`
- 音频：`assets/news_audio/2026_07_23/manifest.json`
- 微软语音：`zh-CN-XiaoxiaoNeural`
- 语速：正常语速 `+0%`
- 新闻数量：6 条

### 一个 block 的定义

一个新闻 block 是按照新闻文件顺序呈现全部 6 条新闻，每条新闻呈现一次。
当前新闻范式运行一个 block，不随机排序，也不会自动重复。

### 每个 block 内的新闻 trial 流程

每条新闻按以下流程运行：

1. 屏幕显示较小的白色新闻文字和小红色正方形。
2. 画面保持 0.5 秒。
3. 整条新闻音频开始播放；新闻页面和红方块保持不变。
4. 音频结束后继续保持新闻页面 1.0 秒。
5. 进入最短休息阶段，默认继续显示刚才的新闻页面。
6. “下一条”按钮立即显示，但在随机 5.0–6.0 秒内不可点击，并显示倒计时。
7. 最短休息结束后按钮启用。
8. 鼠标移到按钮上时，按钮变亮并显示手形光标。
9. 患者或实验人员必须点击按钮，才会显示下一条新闻；不会自动翻页。
10. 最后一条新闻的按钮文字为“结束”，点击后保存结果并退出范式。

如果希望休息阶段显示黑底灰色十字：

```powershell
python scripts\run_relaxing_news.py --rest-screen cross
```

两种休息背景都保留倒计时和继续按钮：

```text
--rest-screen news     默认，保留刚才的新闻页面
--rest-screen cross    黑底灰色十字
```

新闻范式使用 `Esc` 退出。普通鼠标点击不会退出；鼠标仅用于点击启用后的
“下一条”或“结束”按钮。

常用调整：

```powershell
python scripts\run_relaxing_news.py `
  --font-size 36 `
  --square-size 80 `
  --rest-screen news `
  --rest-min 5 `
  --rest-max 6
```

## 实验前检查

给患者正式运行前，请检查：

1. 已激活 `experiment_paradigm` Conda 环境。
2. Windows 扬声器已选择正确，系统音量合适。
3. 关闭通知、聊天软件弹窗和自动更新提示。
4. 自己先试听一遍目标音频。
5. 确认使用的是正确刺激和 manifest。
6. 确认 `timestamp/` 可写。
7. 让实验人员知道按 `Esc` 可以紧急退出。

查看全部参数：

```powershell
python scripts\run_sentence_audio_zh.py -h
python scripts\run_relaxing_news.py -h
```

## 结果文件

每次完成的 trial 都会写入：

```text
timestamp/<范式名称>_<日期时间>.csv
timestamp/<范式名称>_<日期时间>.json
```

闭锁范式结果包含刺激编号、block（`repetition`）、block 内 trial 编号、音频
事件、进度事件、随机时长和实际时长。

新闻范式结果还包含最短休息时长、按钮启用时间、按钮点击时间、实际总休息
时长，以及最短休息结束后额外等待的时间。
