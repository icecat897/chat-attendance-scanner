# Chat Attendance Scanner

本项目是一个本地网页工具，用来分析 QQ / 微信聊天长截图，识别哪些成员在聊天记录中发过图片消息，并统计未出现人员。

它适合这类场景：

- 班级或小组活动签到
- 成员需要在群聊里发送现场照片
- 你已经有一份成员名单，希望自动排除组长和请假人员
- 你更在意本地可用、识别稳定，而不是纯前端云端部署

## 主要功能

- 读取 `成员.md` 作为成员名单
- 自动忽略名字后带 `（组长）` 的成员
- 每次分析时可额外输入请假人员
- 支持 QQ / 微信聊天长截图上传
- 服务端本地 OCR 识别昵称
- 支持昵称包含姓名的情况，例如 `计科2401吴宇珂`
- 支持轻微 OCR 错字模糊匹配，例如 `信安2401蓝林哗 -> 蓝林晔`
- 未稳定识别的昵称可手动映射，并记忆到 `data/mappings.json`

## 当前方案为什么稳定

当前版本不是浏览器端 OCR，而是：

- 前端：上传截图、输入请假人员、展示统计结果
- 后端：`FastAPI + RapidOCR + OpenCV`

这样做的好处是：

- 长截图识别更稳定
- 中文昵称识别效果明显好于纯浏览器方案
- 不依赖前端模型加载和浏览器性能
- 更适合你的实际使用场景

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

或者直接双击：

- `start.bat`

### 3. 打开网页

本机访问：

```text
http://127.0.0.1:8000
```

## 使用流程

1. 准备 `成员.md`
2. 打开网页并上传聊天长截图
3. 输入本次请假人员
4. 点击“开始分析”
5. 查看：
   - 已出现人员
   - 未出现人员
   - 已排除人员
   - 识别明细

## 成员名单格式

推荐格式：

```text
1. 朱文彬
2. 吴宇珂（组长）
3. 谢俊邦
```

也支持简单格式：

```text
朱文彬
吴宇珂（组长）
谢俊邦
```

说明：

- 带 `（组长）` 的成员会自动排除
- 修改 `成员.md` 后，不需要重启服务
- 如果网页已经打开，建议手动刷新一次页面再继续使用

## 手机使用

### 同一局域网

如果手机和电脑在同一个 Wi-Fi 下：

1. 在电脑上启动项目
2. 查电脑局域网 IP，例如 `192.168.1.10`
3. 手机浏览器打开：

```text
http://192.168.1.10:8000
```

### 不在同一局域网

推荐使用 `Cloudflare Tunnel`。

安装 `cloudflared` 后，直接双击：

- `start_public.bat`

它会：

- 启动本地服务 `http://127.0.0.1:8000`
- 再启动一个临时公网 tunnel

当窗口里出现类似：

```text
https://xxxx-xxxx.trycloudflare.com
```

把这个地址发到手机浏览器打开即可。

注意：

- 电脑必须保持开机
- 本地服务窗口不能关闭
- tunnel 窗口不能关闭
- 临时公网地址重启后通常会变化

## GitHub 上传建议

推荐上传这些文件：

- `app.py`
- `requirements.txt`
- `static/`
- `scripts/debug_rapidocr.py`
- `成员.md`
- `README.md`
- `start.bat`
- `start_public.bat`

以下内容已加入 `.gitignore`，默认不会上传：

- `图片/`
- `data/mappings.json`
- `uvicorn.log`
- `__pycache__/`

## 部署说明

这个项目当前不能直接原样部署到 Cloudflare Pages，因为它依赖：

- Python
- FastAPI
- OpenCV
- onnxruntime
- RapidOCR

如果你以后想做固定公网访问，更适合：

1. 代码托管到 GitHub
2. Python 后端部署到支持 Python 的平台，例如 `Render`、`Railway`、`Fly.io`
3. 再用 Cloudflare 做域名解析和反向代理

## 目录说明

- `app.py`：后端主程序
- `static/`：网页前端文件
- `成员.md`：成员名单
- `data/mappings.json`：昵称手动映射记忆
- `start.bat`：本地启动脚本
- `start_public.bat`：本地服务 + Cloudflare Tunnel 启动脚本

## 已验证样例

以示例长截图 `9de6b9a02714e44c1ae71fe84bbd6d06_720.jpg` 为例，在请假人员为：

```text
朱文彬 岳瑶淇 蔡承翰 胡帅珂 谭睿
```

当前版本可回归到：

- 已出现 27 人
- 未出现仅 `栗嘉影`

## License

如需公开仓库，建议你自行补充许可证，例如 `MIT`。
