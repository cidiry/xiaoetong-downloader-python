# 小鹅通下载链接提取工具

一个基于 Tkinter 的轻量桌面工具，用于从已购课程中选择子课程与视频/直播资源，并提取对应的播放/下载链接。

## 功能特点

- 加载已购课程列表
- 选择子课程并查看可处理资源
- 支持视频/直播多选批量获取链接
- 支持线程数和批次延迟配置
- 支持导出为 `子课程名.txt`
- 支持保存 cookies 配置并在下次启动时自动加载

## 运行环境

- Python 3.10+
- Windows（当前界面和使用场景主要按 Windows 使用方式设计）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动方式

```bash
python main.py
```

## 配置说明

项目运行依赖小鹅通站点的 cookies 信息。

首次使用时：

1. 启动程序
2. 在界面顶部粘贴完整 cookies 字符串
3. 点击“保存 Cookies”
4. 再点击“加载已购课程”

程序会自动从 cookies 中提取并保存：

- `app_id`
- `user_id`
- `base_url`
- `cookies`
- `cookie_string`

本地配置文件默认保存为：

- `config.json`


可参考仓库中的示例文件：

- `config.example.json`

## 使用流程

1. 保存 cookies 配置
2. 加载已购课程
3. 选择一个子课程
4. 在右侧选择一个或多个视频/直播资源
5. 设置线程数和延迟时间
6. 点击“获取所选视频/直播链接”
7. 按需导出 txt 文件
8. 使用m3u8下载工具批量下载视频资源，推荐https://github.com/Harlan-H/M3u8Downloader_H（v4.0.3版本）

## 线程与延迟说明

- 线程数范围：`1 ~ 20`
- 延迟范围：`0.0s ~ 5.0s`
- 当前实现为“分批并发”模式：
  - 每一批最多执行 `N` 个任务（`N = 线程数`）
  - 当前批次全部完成后，再等待设定延迟
  - 然后继续下一批

线程越少通常越稳，越不容易触发站点风控或请求异常。

## 项目结构

```text
main.py   # 启动入口
gui_app.py          # Tkinter 图形界面
link_service.py     # 业务编排与导出逻辑
xiaoetong_api.py    # 接口请求层
app_config.py       # 本地配置读写与 cookies 解析
config.example.json # 配置示例
requirements.txt    # 依赖列表
```


## 免责声明

本项目仅供学习界面开发、请求编排和本地工具开发使用。请在遵守目标平台协议、版权约束和当地法律法规的前提下使用。
