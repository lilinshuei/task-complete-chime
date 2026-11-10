---
name: task-complete-chime
version: 1.4.0
display_name: 任务完成提示音
display_name_en: Task Completion Chime
description: 任务完成提示音：Agent 完成或失败一项任务、准备给出最终回复时，自动播放一段短提示音。默认内置 12 秒原创铃声，也可指定本地音频；成功、失败、纯问答都会响，仅用户要求安静时不播。
description_zh: >-
  当 Agent 完成或失败一项用户任务、准备给出收尾回复时，自动播放一段短提示音。
  默认使用内置的 12 秒原创铃声（assets/chime.wav），也可以用 --audio 指定自己的本地音频。
  成功、失败、未完成、纯问答都会响，仅用户明确要求安静时不播。
description_en: >-
  Play a short chime whenever an agent finishes or fails a task and is about to
  give its final answer. Ships with an original 12-second chime; pass --audio to
  use your own local file. Fires on success, failure, unfinished work and plain
  Q&A, unless the user explicitly asks for quiet.
examples_zh:
  - "干完活自动响一下，不用一直盯着屏幕等结果"
  - "任务失败了也响，提醒我这一轮有结论了"
  - "同时挂好几个任务跑，靠耳朵就能分清哪个处理完了"
examples_en:
  - "Play a short chime when the task is done, so I don't keep watching the screen"
  - "Also chime on failure, so I know there is a result to check"
  - "Run several tasks in parallel and tell which one finished by ear"
author: "lilinshuei"
---

# 任务完成提示音 · task-complete-chime

## 这是什么

Agent 每完成（或失败）一件你交代的事、准备给出最终回复时，自动播放一段 12 秒的提示音。不用点、不用喊，声音一响，你就知道该去看结果了。

默认铃声是本项目内置的原创 chime（`assets/chime.wav`），不包含任何第三方音乐片段。想换成自己的音频，用 `--audio` 指定本地文件即可。

## 什么时候响

| 场景 | 是否播放 | 说明 |
|---|---|---|
| 任务完成、即将给出最终回复 | ✅ | 最常见的「干完了」提醒 |
| 任务失败 / 未完成，已给结论 | ✅ | 失败也响，提醒这一轮有结果 |
| 纯问答、只回了一句话 | ✅ | 每轮结束都响 |
| 用户明确说「别播 / 安静 / 关掉提示音」 | ❌ | 唯一豁免 |
| Agent 中途思考、循环中间步骤 | ❌ | 只在收尾那一下响 |

**铁律**：一次任务只响一次；多个步骤只在最后收尾响；纯问答每轮结束响一次。

## 怎么用

需要 Windows + Python 3.9 及以上，**只用标准库**，不需要 pip 安装任何包。

```powershell
# 默认：播放内置 12 秒铃声
python scripts/chime.py

# 换成自己的音频（WAV 直接播；MP3/MP4 需要 ffmpeg 在 PATH 中）
python scripts/chime.py --audio "C:\path\to\your.wav"

# 只播 8 秒 / 播完整首
python scripts/chime.py --seconds 8
python scripts/chime.py --full

# 立刻停掉正在播的提示音
python scripts/chime.py --stop
```

- 日志：`%LOCALAPPDATA%\task-complete-chime\chime.log`
- 停止标记：`%LOCALAPPDATA%\task-complete-chime\STOP`
- 非 WAV 音频会先用 ffmpeg 转成临时 WAV；没有 ffmpeg 时请直接提供 `.wav`。

## 三条停止通道

1. `--stop` 写入停止标记，播放进程约 0.1 秒内停止。
2. 播满指定时长自然结束。
3. `Ctrl+C` 中断。

## 设计边界

- **离线**：不联网、不上传、不写注册表、不改系统设置。
- **零删除**：只新增日志和临时 WAV，不删除任何现有文件。
- **不抢焦点**：异步播放，不弹窗、不阻塞 Agent 的最终回复。
- **可替换音源**：默认音源是原创合成铃声；想用自己的歌，自行确保拥有相应使用权。

## 目录结构

```
task-complete-chime/
├── SKILL.md              # 技能定义
├── assets/
│   └── chime.wav         # 内置原创 12 秒铃声
└── scripts/
    └── chime.py          # 播放 / 停止脚本（仅标准库）
```

## 验收

```powershell
python scripts/chime.py --seconds 2
```

应听到约 2 秒声音，并在日志中看到 `play_start` 与 `play_end` 两行；若只有 `play_start`，检查系统输出设备是否被独占。
