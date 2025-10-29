# pip-fc

> pip-fc 全称是：pip fast check

`pip-fc` 是一个轻量级的 Python 工具，旨在测试多个镜像源的连接速度，并帮助用户选择最快的镜像源进行软件包安装。支持 Python 2.7 和 3.x 版本，能够自动根据环境选择适合的并发模式（`asyncio` 或 `threading`）。

---

## 功能

- 测试多个镜像源的连接速度。
- 自动选择连接速度最快的镜像源。
- 支持 Python 2.7 和 3.x 版本。
- 使用异步（`asyncio`）或线程池（`threading`）来提高测试效率。
- 简单易用的命令行界面。

## 安装

### 使用 `pip` 安装：

```bash
pip install pip-fc
```

## 使用方法

通过运行以下命令启动：

`pip-fc` 或者 `python -m pip-fc`

此命令将会测试预设的镜像源，并显示连接速度最快的镜像源。你也可以自定义镜像源进行测试。

### 设置全局镜像源

如果你希望将测试中找到的最快镜像源设置为全局 `pip` 镜像源，可以在运行完成后输入 `y` 来确认：

```bash
Do you want to set the fastest mirror as the global pip mirror? (y/n): y
```

此操作将更新 `pip` 的配置文件，设置全局镜像源和回退镜像源。

## 依赖

* `pip`：用于安装和管理 Python 包。
* `futures`：仅在 Python 2.7 环境下需要，安装时自动处理。

## 示例输出

```
Detected Python Version: 3.8.5 (asyncio)
--- Starting connection speed test using asyncio mode ---
Successfully tested 6 mirrors.
Fastest Mirror: https://pypi.tuna.tsinghua.edu.cn/simple/
Latency: 50.12345 ms

--- All Successful Connection Results (URL, Latency in ms) ---
  https://pypi.tuna.tsinghua.edu.cn/simple/: 50.12345 ms
  https://mirrors.aliyun.com/pypi/simple/: 65.67890 ms
  ...
```

## 贡献

欢迎提出问题、提交 bug 或者贡献代码。如果你有任何问题，或者希望添加新特性，请提交 [issue](https://github.com/harmonsir/pip-fc/issues)。

## 许可

该项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。
