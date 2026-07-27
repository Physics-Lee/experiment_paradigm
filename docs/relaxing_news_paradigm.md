# 新闻放松朗读范式

## 用途

该范式用于患者被动放松。每个 trial 显示一条新闻和一个小红色正方形，并使用
预先生成的 Microsoft Edge 神经语音整句朗读。患者不需要跟读。

## 默认输入

- 新闻刺激：`stimuli/news/2026_07_23.md`
- 音频目录：`assets/news_audio/2026_07_23/zh-CN-YunyangNeural/`
- 音频清单：
  `assets/news_audio/2026_07_23/zh-CN-YunyangNeural/manifest.json`
- 语音：`zh-CN-YunyangNeural`
- 语速：`+0%`
- TTS 单元：整条新闻

新闻输入可以是每个非空行一条新闻的纯文本，也可以是 Markdown 表格。
Markdown 表格会自动读取列名中包含“标题”的一列，并跳过表头和其他列。

## 生成音频

从仓库根目录运行：

```powershell
python scripts/generate_news_audio.py
```

生成阶段需要网络；音频和 manifest 完整生成后，正式播放阶段不需要网络。
文字、语音设置和 SHA-256 都匹配时，已有音频会被复用。

## 运行

```powershell
python scripts/run_relaxing_news.py
```

按 `Esc` 退出。完成的 trial 会保存到 `timestamp/` 下的 CSV 和 JSON 文件。

## 默认 trial 流程

1. 白色新闻文字与红色正方形同时出现。
2. 画面保持 0.5 秒。
3. 正常语速音频开始，文字和方块保持不变。
4. 音频结束后继续保持画面 1.0 秒。
5. 默认继续显示刚才的新闻页面，同时显示禁用的“下一条”按钮。
6. 随机休息 5.0–6.0 秒后按钮启用；患者必须点击按钮才会进入下一条新闻。
7. 最后一条新闻显示“结束”按钮，点击后结束范式。

方块在新闻呈现阶段始终为红色；该范式没有绿色状态、跟读进度条或提示音。
休息计时是按钮启用前的最短时间；患者未点击时，当前页面会继续保留。

如果需要恢复黑底灰色十字休息画面：

```powershell
python scripts/run_relaxing_news.py --rest-screen cross
```

`--rest-screen news` 和 `--rest-screen cross` 都需要点击按钮才会继续。

## 常用参数

```powershell
python scripts/run_relaxing_news.py -h

python scripts/run_relaxing_news.py `
  --font-size 36 `
  --square-size 80 `
  --rest-screen news `
  --rest-min 5 `
  --rest-max 6
```

较长新闻会自动换行；当最大字号无法容纳文字时，范式会继续缩小字号。

## 更换新闻

建议将新文件放在 `stimuli/news/`，并为它使用独立的日期音频目录：

```powershell
python scripts/generate_news_audio.py `
  --news "stimuli/news/2026_07_24.md" `
  --output-dir "assets/news_audio/2026_07_24/zh-CN-YunyangNeural" `
  --voice zh-CN-YunyangNeural

python scripts/run_relaxing_news.py `
  --news "stimuli/news/2026_07_24.md" `
  --audio-dir "assets/news_audio/2026_07_24/zh-CN-YunyangNeural"
```

不要让新刺激文件继续使用旧日期的 manifest；启动时会校验文字和顺序，
不匹配时会拒绝进入全屏。
