import socket
import subprocess
import sys
import time
from urllib.parse import urlparse


__PYTHON_VERSION = sys.version_info

# 兼容性导入和版本检查
if __PYTHON_VERSION >= (3, 8):
    CONCURRENCY_MODE = "asyncio"
elif __PYTHON_VERSION >= (3, 0):
    CONCURRENCY_MODE = "threading_py3"
else:
    CONCURRENCY_MODE = "threading_py2"

# do import
if CONCURRENCY_MODE == "asyncio":
    import asyncio
elif CONCURRENCY_MODE == "threading_py3":
    from concurrent.futures import ThreadPoolExecutor  # noqa
else:
    try:
        # 尝试导入 Python 2.7 兼容库
        from futures import ThreadPoolExecutor
        from Queue import Queue

    except ImportError:
        CONCURRENCY_MODE = "unsupported"

# Core
MAX_LATENCY = float("inf")

MAIN = [
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/",
    "https://repo.huaweicloud.com/repository/pypi/simple/",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.mirrors.ustc.edu.cn/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
]

BACKUP = [
    "https://pypi.doubanio.com/simple/",
    "https://mirrors.163.com/pypi/simple/",
    "https://mirror.baidu.com/pypi/simple/",
]

ALL_MIRRORS = set(MAIN + BACKUP)


class MirrorTester:
    """
    兼容 Python 2.7 到 3.x 的镜像源测速器。
    根据 Python 版本自动选择 asyncio (>=3.8) 或 ThreadPoolExecutor (<=3.7)。
    """

    def __init__(self, urls, timeout=5.0):
        self.urls = urls
        self.timeout = timeout
        self.results = []
        self.mode = CONCURRENCY_MODE

        print("Detected Python Version: {}.{}.{} ({})".format(*sys.version_info[:3], self.mode))
        print("{}\n".format("= " * 20))

        self.__fastest_url = None

    @property
    def fastest_url(self):
        return self.__fastest_url

    def _parse_url(self, url):
        """解析URL，返回主机名和端口。"""
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if host.startswith("https://") else 80)
        if not host:
            raise ValueError("Invalid URL host: {}".format(url))

        return host, port

    # --- 核心同步测速函数 (用于 Threading/Fallback) ---

    def _test_connection_sync(self, url):
        """使用同步 socket 测试单个连接速度。"""
        try:
            host, port = self._parse_url(url)
            ip = socket.gethostbyname(host)
        except Exception:
            return url, MAX_LATENCY

        start_time = time.time()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((ip, port))
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # 转换为毫秒
            return url, round(latency, 2)
        except Exception:
            return url, MAX_LATENCY
        finally:
            sock.close()

    # --- 异步执行器 (Asyncio >= 3.8) ---

    async def _test_connection_async(self, url):
        """使用 asyncio 测试单个连接速度。"""
        try:
            host, port = self._parse_url(url)
            ip = socket.gethostbyname(host)
        except Exception:
            return url, MAX_LATENCY

        start_time = time.time()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=self.timeout
            )
            end_time = time.time()
            latency = (end_time - start_time) * 1000

            writer.close()
            await writer.wait_closed()
            return url, round(latency, 2)
        except Exception:
            return url, MAX_LATENCY

    async def _run_async(self):
        """并行运行所有异步测试任务。"""
        tasks = [self._test_connection_async(url) for url in self.urls]
        return await asyncio.gather(*tasks)

    # --- 主执行逻辑 ---

    def compare_connection_speeds(self):
        """根据 Python 版本选择执行模式。"""

        if self.mode == "unsupported":
            print("Error: Python version is too old (< 2.7 or missing 'futures' dependency for 2.7). Cannot proceed.")
            return

        print("--- Starting connection speed test using {} mode ---".format(self.mode))

        if self.mode == "asyncio":
            # 优先使用 asyncio
            try:
                # asyncio.run 存在于 3.7+，但我们只在 >=3.8 时才启用此分支
                self.results = asyncio.run(self._run_async())
            except Exception as e:
                print("Asyncio execution failed: {}. Falling back to Threading.".format(e))
                self.results = self._run_sync_executor()

        elif self.mode.startswith("threading"):
            # 使用 ThreadPoolExecutor (兼容 2.7 和 3.x)
            self.results = self._run_sync_executor()

        self._report_results()

    def _run_sync_executor(self):
        """使用 ThreadPoolExecutor 运行同步测试。"""
        max_workers = min(32, len(self.urls))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._test_connection_sync, url) for url in self.urls]

            results = [future.result() for future in futures]
            return results

    def _report_results(self):
        """报告最终结果。"""
        if not self.results:
            print("No results were gathered.")
            return

        print("\n--- Speed Test Results Summary ---")

        successful_results = [r for r in self.results if r[1] != MAX_LATENCY]

        if successful_results:
            # 兼容 2.7 和 3.x 的 min 函数
            fastest_url, min_latency = min(successful_results, key=lambda x: x[1])
            self.__fastest_url = fastest_url

            print(f"The fastest mirror is: {fastest_url}")
            print(f"Latency: {min_latency:.2f} ms")

            sorted_results = sorted(successful_results, key=lambda x: x[1])
            print("\n--- All Successful Connection Results (URL, Latency in ms) ---")
            for url, latency in sorted_results:
                print(f"  {url}: {latency:.2f} ms")
        else:
            print(
                "Error: All mirror connections have failed or timed out."
                "Please check your network or try again later."
            )


def set_global_pip_mirror(mirror_url, backup_mirror_url="https://pypi.org/simple"):
    """设置 pip 全局镜像源并添加备份为 PyPI 的配置"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "config", "set", "global.index-url", mirror_url])
        print(f"Global pip mirror has been successfully set to: {mirror_url}")

        subprocess.check_call(
            [sys.executable, "-m", "pip", "config", "set", "global.extra-index-url", backup_mirror_url]
        )
        print(f"Backup mirror has been successfully set to: {backup_mirror_url}")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while setting pip mirror: {e}")
        return False

    return True


def core_main():
    if CONCURRENCY_MODE == "threading_py2" and "futures" not in sys.modules:
        print(
            "Warning: Running on Python 2.7. "
            "Please ensure that the 'futures' library is installed using `pip install futures`."
        )

    tester = MirrorTester(urls=ALL_MIRRORS)
    tester.compare_connection_speeds()

    print("\n{}\n".format("= " * 20))
    inp = input("Do you want to set the fastest mirror as the global pip mirror? (y/n): ")
    if inp.lower() == "y":
        set_global_pip_mirror(mirror_url=tester.fastest_url)


if __name__ == "__main__":
    core_main()
