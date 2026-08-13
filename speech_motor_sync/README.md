# 说话与运动同步范式（speech_motor_sync）

一个独立自包含的全屏 Pygame 实验范式，**不依赖** 仓库里的 `experiment_paradigm`
包。把整个 `speech_motor_sync/` 文件夹打包发给同事，对方安装 `pygame` 后即可运行。

## 任务

每个 trial 屏幕上同时呈现：**左侧一个中文数字**（一~十）和**右侧对应的手势图**；
屏幕最下方有一条长方形 go-cue。流程：

1. 第一个 trial 前先黑屏静息基线。
2. **准备期**：左汉字 + 右手势图 + 底部**红色**长方形。
3. **Go cue**：长方形由**红变绿**（可伴随统一“滴”声）→ 受试者**同步说出该数字并
   做出对应手势**。
4. 保持刺激 + 绿条一段反应窗，供采集/分析。
5. trial 间休息（默认“下一条/结束”按钮，休息满最短时长后点亮）。

所有相位的时间戳都会写到 `timestamp/` 下的成对 CSV/JSON。

## 屏幕布局

```
┌──────────────────────────────────────────────┐
│                                              │
│     一（汉字，居左）        [手势图，居右]      │
│                                              │
│                                              │
│      ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇  ← go-cue 长方形  │
└──────────────────────────────────────────────┘
        红 = 准备期      绿 = go/反应窗
```

## 运行

```bash
pip install -r requirements.txt      # 仅需 pygame==2.6.1
python run.py                        # 默认参数
```

按 `Esc` 或关闭窗口退出。鼠标点击仅在“下一条/结束”按钮上生效（休息到点后点亮）。

常用示例：

```bash
python run.py --repetitions 3                 # 循环 3 轮
python run.py --no-cue-tone                   # 关闭 go-cue 提示音
python run.py --response-duration 2.5         # 加长反应窗
python run.py --no-continue-button            # 回到定时休息（无按钮）
```

## 手势图片

`gestures/01.jpeg`~`gestures/10.jpeg` 当前是**真实手势照片**，与 `stimuli.txt` 的第
1~10 行一一对应。支持 `.jpg`/`.jpeg`/`.png`（同名时真实照片优先于生成图）。把照片按
`01`~`10` 编号直接覆盖即可，**无需改代码**。详见 `gestures/README.md`。

如需重新生成矢量示意图（会覆盖为 `.png`）：

```bash
python make_gestures.py
```

若运行时某个编号图片缺失，范式会在右侧即时绘制一张带编号的占位卡片，不会崩溃，并
把该 trial 在结果里标记为 `gesture_placeholder=true`。

## 主要 CLI 参数（默认值见 `python run.py --help`）

| 分组 | 参数 |
| --- | --- |
| 显示 | `--display-mode {borderless,exclusive}` |
| 刺激/输出 | `--stimuli` `--gestures-dir` `--output-prefix` `--output-dir` |
| 循环与顺序 | `--repetitions` `--shuffle`/`--no-shuffle` |
| 视觉与提示 | `--font-size` `--show-rest-cross`/`--no-rest-cross` `--continue-button`/`--no-continue-button` `--show-continue-countdown` |
| 试次时序（秒） | `--baseline-min/max` `--prep-min/max` `--response-duration` `--rest-min/max` |
| 统一提示音 | `--no-cue-tone` `--cue-frequency` `--cue-duration` `--cue-volume` |

默认时序：基线 1.5~2.5s（仅首 trial）、准备期 1.5~2.0s、反应窗 2.0s、休息 5~6s；
提示音 1000Hz/0.08s/音量 0.7；每轮默认随机打乱、循环 1 次。

## 输出字段（每 trial，CSV + JSON）

`trial_id, stimulus_index, repetition, repetition_trial, paradigm, character,
gesture_file, gesture_placeholder, trial_start(_abs),
planned/actual_baseline_duration, baseline_applied,
prep_onset(_abs), prep_offset(_abs), planned/actual_prep_duration,
go_onset(_abs)`（go cue 变绿 + 提示音 + 说话/运动起始对齐标记）
`, response_offset(_abs), actual_response_duration,
planned/actual_rest_duration, rest_cross_enabled, continue_button_* 事件,
cue_tone_enabled/onset(_abs), font_size, bar_x/y/width/height,
display_width/height, trial_end(_abs)`。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `run.py` | 命令行入口（argparse + `main`） |
| `paradigm.py` | 自包含范式实现（含最小 base/字体/时序/结果/提示音） |
| `make_gestures.py` | 重新生成矢量手势示意图（非全屏，安全可重跑） |
| `stimuli.txt` | 刺激列表（一~十，每行一个） |
| `gestures/` | 手势图片（占位图，可替换） |
| `timestamp/` | 运行时生成的 CSV/JSON（被 `.gitignore` 忽略） |
