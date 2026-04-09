# GitHub Repo Copy

## 仓库名候选

优先推荐：

- `chat-attendance-scanner`
- `qq-wechat-attendance-scanner`
- `group-photo-checkin-scanner`

如果你想更偏中文语义：

- `chat-image-checkin`
- `group-checkin-ocr`
- `member-presence-scanner`

如果你想保留一点“签到”语感：

- `photo-checkin-tracker`
- `attendance-by-chat-image`
- `chat-photo-attendance`

我的建议：

- 仓库名首选：`chat-attendance-scanner`

原因：

- 简洁
- 不局限 QQ / 微信
- 后续如果你扩展到别的聊天软件也不违和
- GitHub 上看起来比较专业

## GitHub About 文案

### 简短版

Analyze QQ/WeChat chat screenshots, detect members who posted image messages, and list absentees.

### 中文版

分析 QQ / 微信聊天长截图，识别发过图片消息的成员，并统计未出现人员。

## 仓库描述

一个基于 FastAPI、RapidOCR 和 OpenCV 的本地网页工具，用于分析聊天长截图中的图片签到记录，支持成员名单、组长排除、请假排除、昵称模糊匹配和手动映射记忆。

## 仓库标签建议

- `fastapi`
- `ocr`
- `opencv`
- `python`
- `attendance`
- `wechat`
- `qq`
- `screenshot`
- `rapidocr`

## 建议置顶介绍

Chat Attendance Scanner is a local web tool for analyzing QQ/WeChat chat screenshots and identifying which members have posted image messages.

It is designed for practical attendance workflows where participants send photos in a group chat, and the system automatically filters leaders, handles leave members, and outputs a missing-members list.

## 首个提交信息建议

```text
Initial chat attendance scanner
```

## 后续提交信息风格建议

- `improve OCR matching for rare Chinese names`
- `add Cloudflare Tunnel startup script`
- `refine member list parsing and exclusions`
- `improve screenshot attendance result display`
