## 新范式：说话与运动同步（speech_motor_sync）

独立自包含文件夹，**不依赖** `experiment_paradigm` 包；同事只需 `pip install pygame` + 该文件夹即可运行/打包发送。无 TTS（纯视觉，受试者在 go cue 时自己同步说出数字并做手势）。

### 文件结构（仓库根下新建 `speech_motor_sync/`）
```
speech_motor_sync/
├── run.py                # argparse CLI + main()（自包含入口）
├── paradigm.py           # SpeechMotorSyncParadigm + 内嵌的最小 base/display/results/cue-tone
├── make_placeholders.py  # 重新生成 gestures/01.png..10.png 占位图（非全屏，可随时重跑）
├── stimuli.txt           # 一/二/三/四/五/六/七/八/九/十，每行一个
├── gestures/
│   ├── 01.png … 10.png   # 10 张占位手势卡（生成、可替换）
│   └── README.md         # 如何用真实手势照片替换（保持 01.png..10.png 命名）
├── requirements.txt      # pygame==2.6.1（无需 edge-tts/mutagen）
├── README.md             # 用法、布局图、时序、CLI、输出字段说明
├── .gitignore            # 忽略 timestamp/、__pycache__/
└── timestamp/            # 运行时生成 CSV/JSON（被忽略）
```

### 单 trial 时序（参考闭锁范式，全部秒）
1. **基线**（仅第一个 trial）：黑屏 `baseline_min~max`（默认 1.5~2.5）
2. **准备期 prep**：左侧汉字 + 右侧手势图 + 底部**红色**长方形 go-cue 条，持续 `prep_min~max`（默认 1.5~2.0，随机）
3. **GO**：底部条由**红变绿**，同时可选统一“滴”声（1000Hz/0.08s/音量0.7，默认开）→ 受试者**同步说出该数字并做出手势**；保持 `response_duration`（默认 2.0s）作为反应窗
4. **休息**：默认“下一条/结束”按钮（休息满 `rest_min~max` 默认 5~6s 后点亮），可选灰色十字（默认开）；也支持回到定时休息
- 其余：`repetitions`（默认1）、每轮 `shuffle`（默认开）、`font_size`（默认300）、`display-mode`（默认 borderless）

### 屏幕布局
- 上方内容区：汉字居左（center_x≈0.28W，按左半区自适应字号、白色），手势图居右（center_x≈0.72W，保持长宽比缩放进右半区方框）
- 底部 go-cue 长方形：x≈0.1W、宽≈0.8W、高≈max(60,0.07H)，贴近底部；prep=红、go/反应=绿
- 基线/休息：黑屏（休息可显灰十字）

### 手势图处理（按你的选择：生成占位图）
- `make_placeholders.py` 用 pygame 画 800×800 占位卡（边框 + 中文数字 + 阿拉伯数字 + “手势占位图 N · 请替换”），`pygame.image.save` 存为 PNG。**现在运行一次**生成并提交这 10 张。
- 运行时加载 `gestures/{nn:02d}.png`（第 i 行刺激 ↔ 第 i 张）；**若文件缺失则即时绘制同款占位卡**，绝不崩溃，并在记录里标 `gesture_placeholder=true`。
- 同事把真实手势照片按 `01.png..10.png` 覆盖即可，代码不变。

### 记录字段（每 trial，分析就绪，CSV+JSON 落到 `timestamp/`）
`trial_id, stimulus_index, repetition, repetition_trial, paradigm="speech_motor_sync", character, gesture_file, gesture_placeholder, trial_start(_abs), planned/actual_baseline_duration, baseline_applied, prep_onset(_abs), prep_offset(_abs), planned/actual_prep_duration, go_onset(_abs)`（条变绿+提示音+说话/运动起始标记）`, response_offset(_abs), actual_response_duration, planned/actual_rest_duration, rest_cross_enabled, continue_button_* 事件, cue_tone_enabled/onset(_abs), font_size, bar 几何, display_width/height, trial_end(_abs)`。

### CLI（run.py，分组中文 help，仿闭锁范式）
组：显示设置 / 刺激与输出（`--stimuli` 默认 `stimuli.txt`、`--gestures-dir` 默认 `gestures`、`--output-prefix`）/ 循环与顺序（`--repetitions`、`--shuffle`/`--no-shuffle`）/ 视觉与提示（`--font-size`、`--show-rest-cross`/`--no-rest-cross`、`--continue-button`/`--no-continue-button`、`--show-continue-countdown`）/ 试次时序（`--baseline-min/max`、`--prep-min/max`、`--response-duration`、`--rest-min/max`）/ 统一提示音（`--no-cue-tone`、`--cue-frequency/duration/volume`）。默认路径相对该文件夹。

### 自包含实现要点（paradigm.py，从现有包裁剪、无外部依赖）
内嵌：CJK 字体回退表+`load_cjk_font`、`show_for_duration`/`validate_duration_range`、`draw_cross`、`write_csv/write_json/write_run_results`、闭锁式 `_create_cue_sound`（math+struct+pygame.mixer）、最小 base（borderless 全屏、时钟、`get_timestamp`/`get_absolute_time`、`save_data`、`check_exit_events`、`show_interval`、继续按钮交互）。`SpeechMotorSyncParadigm` 含 `_build_trial_schedule`（repetitions+shuffle）、`_draw_trial_state(char, gesture, bar_color)`、`display_trial`、`run`。ESC/关窗退出，鼠标点击仅通过按钮推进（与闭锁一致）。

### 验证（遵守“不全屏自动运行”约定）
- 对新 .py 做 AST 语法检查（沿用仓库既有写法）
- 运行 `make_placeholders.py`（非全屏）生成 10 张 PNG
- 运行 `python speech_motor_sync/run.py --help`（解析后即退出，不开窗）验证 CLI
- 可选：`SDL_VIDEODRIVER=dummy` 下仅**构造**对象+构建 schedule（**不调用 run()**）以捕获错误

### 不改动的内容
不动现有 `src/experiment_paradigm/`、`scripts/`、`pyproject.toml` 及任何既有素材/数据，保持该文件夹可独立剥离发送。