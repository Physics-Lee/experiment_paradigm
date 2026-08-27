# 说话与运动同步范式（speech_motor_sync）

一个独立自包含的全屏 Pygame 实验范式，**不依赖** 仓库里的 `experiment_paradigm`
包。把整个 `speech_motor_sync/` 文件夹打包发给同事，对方安装 `pygame` 后即可运行。

## 任务

每个 trial 屏幕上同时呈现：**左侧一个中文数字**（一~十）和**右侧对应的手势图**；
屏幕最下方有一条长方形 go-cue。流程：

1. 第一个 trial 前先黑屏静息基线。
2. **准备期**：左汉字 + 右手势图 + 底部**红色**长方形。
3. **目标音频**：播放该数字的 TTS 音频（与闭锁范式同款 `zh-CN-YunxiaNeural`），
   底部条仍为红色。
4. **静默延迟**：保持汉字 + 手势 + 红条。
5. **Go cue**：长方形由**红变绿**（可伴随统一“滴”声）→ 受试者**同步说出该数字并
   做出对应手势**。
6. **反应窗（进度条）**：数字背后出现一道和闭锁范式一样的**浅棕色进度条**，在
   `--speech-progress-duration`（默认 1.2s）内填满；底部条保持绿色，供采集/分析。
7. **终末保持**：进度条填满后保持终末画面 `final_hold`（默认 0.5s），再进入休息屏。
8. trial 间休息（默认“下一条/结束”按钮，休息满最短时长后点亮并显示倒计时，或灰色十字）。

## 任务模式（--task-mode）

| 模式 | go cue | 序列 |
| --- | --- | --- |
| `sync`（默认） | 底部一根红→绿长条 | go 后朗读+手势**同时**进行，汉字背后一道进度条填满 |
| `speak_first`（先朗读再比手势） | 汉字、图片**下方各一个小正方形** | 左侧（朗读）先变绿，汉字背后进度条填满；结束后右侧（手势）变绿，图片下方进度条填满 |
| `gesture_first`（先比手势再朗读） | 同上 | 右侧（手势）先变绿，图片下方进度条填满；随后左侧（朗读）变绿，汉字背后进度条填满 |

序列模式中，每个正方形变绿时各响一次提示音（`--no-cue-tone` 关闭）；**朗读段进度条按
`--speech-progress-duration`（默认 1.2s）、手势段按 `--gesture-progress-duration`
（默认 3.0s，可分别调节）填满**；第一段结束后保持 `inter_phase_interval`
（默认 1.0s，`--inter-phase-interval` 可调）再给第二个 go cue。结果里 `go_onset`
是第一个正方形变绿、`go2_onset` 是第二个；`phase1`/`phase2` 标明各段是 speech 还是
gesture。

```bash
python run.py --task-mode speak_first     # 先朗读再比手势
python run.py --task-mode gesture_first   # 先比手势再朗读
```

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
python run.py --speech-progress-duration 2.5  # 加长朗读进度条
python run.py --speech-progress-duration 1.0 --gesture-progress-duration 2.0  # 两段分别调
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

## 数字音频

每个数字都配一段和闭锁范式同款的神经 TTS 音频（`zh-CN-YunxiaNeural`），存放在
`audio/`，文件名与手势一致（`01.mp3`~`10.mp3`）。生成了**两套语速**：

| 目录 | 语速 | 单字时长（约） |
| --- | --- | --- |
| `audio/slow/` | `-50%`（慢，与闭锁默认一致） | 2.4–2.9 s |
| `audio/normal/` | `+0%`（正常） | 1.25–1.5 s |

默认播放 `audio/normal`（正常语速）。切慢速：

```bash
python run.py --audio-dir audio/slow
```

关闭音频（仅视觉）：

```bash
python run.py --no-audio
```

重新生成音频（需联网 + `pip install edge-tts`，会生成/覆盖 `audio/slow` 与 `audio/normal`）：

```bash
python make_audio.py            # 跳过已存在
python make_audio.py --force    # 强制重新生成
```

## 主要 CLI 参数（默认值见 `python run.py --help`）

| 分组 | 参数 |
| --- | --- |
| 显示 | `--display-mode {borderless,exclusive}` |
| 刺激/手势/音频/输出 | `--stimuli` `--gestures-dir` `--audio-dir` `--no-audio` `--output-prefix` `--output-dir` |
| 循环与顺序 | `--repetitions` `--shuffle`/`--no-shuffle` |
| 视觉与提示 | `--task-mode {sync,speak_first,gesture_first}` `--font-size` `--show-rest-cross`/`--no-rest-cross` `--continue-button`/`--no-continue-button` `--show-continue-countdown` |
| 试次时序（秒） | `--baseline-min/max` `--pre-audio-delay-min/max` `--silent-delay-min/max` `--speech-progress-duration` `--gesture-progress-duration` `--final-hold` `--inter-phase-interval` `--rest-min/max` |
| 统一提示音 | `--no-cue-tone` `--cue-frequency` `--cue-duration` `--cue-volume` |

默认时序：基线 1.5~2.5s（仅首 trial）、音频前延迟 0.9~1.1s、静默延迟 1.9~2.1s、朗读进度条 1.2s、手势进度条 3.0s、终末保持 0.5s、段间隔 1.0s（序列模式）、休息 5~6s；
提示音 1000Hz/0.08s/音量 0.7；每轮默认随机打乱、循环 1 次；音频默认正常语速。

## 输出字段（每 trial，CSV + JSON）

`trial_id, stimulus_index, repetition, repetition_trial, paradigm, character,
gesture_file, gesture_placeholder, trial_start(_abs),
planned/actual_baseline_duration, baseline_applied,
planned/actual_pre_audio_delay, pre_audio_delay_onset(_abs),
audio_enabled, audio_file, audio_onset/offset(_abs),
planned/actual_silent_delay, silent_delay_onset(_abs),
go_onset(_abs)`（go cue 变绿 + 提示音 + 说话/运动起始对齐标记）
`, progress_offset(_abs), planned/actual_progress_duration,
task_mode, phase1/phase2, go2_onset(_abs), cue2_tone_onset(_abs),
actual_phase1/phase2_progress_duration, phase1/phase2_progress_duration_planned,
phase1/phase2_progress_offset(_abs)
（序列模式专用；sync 模式下为空）`,
final_hold_planned/actual_final_hold,
planned/actual_rest_duration, rest_cross_enabled, continue_button_* 事件,
cue_tone_enabled/onset(_abs), font_size, bar_x/y/width/height,
display_width/height, trial_end(_abs)`。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `run.py` | 命令行入口（argparse + `main`） |
| `paradigm.py` | 自包含范式实现（含最小 base/字体/时序/结果/提示音/音频） |
| `make_gestures.py` | 重新生成矢量手势示意图（非全屏，安全可重跑） |
| `make_audio.py` | 重新生成数字 TTS 音频（慢速 + 正常两套；需 edge-tts + 联网） |
| `stimuli.txt` | 刺激列表（一~十，每行一个） |
| `gestures/` | 手势图片（真实照片，可替换） |
| `audio/` | 数字音频（`slow` 慢速 / `normal` 正常两套） |
| `timestamp/` | 运行时生成的 CSV/JSON（被 `.gitignore` 忽略） |
