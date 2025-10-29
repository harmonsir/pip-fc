#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse


__PYTHON_VERSION = sys.version_info

# Compatibility imports and version check
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
        # Attempt to import Python 2.7 compatibility libraries
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

DEFAULT_INDEX_URL = "https://pypi.org/simple"
EXTRA_INDEX_URLS = []


class MirrorTester:
    """
    A mirror source speed tester compatible with Python 2.7 to 3.x.
    Automatically selects asyncio (>=3.8) or ThreadPoolExecutor (<=3.7) based on Python version.
    """

    def __init__(self, urls, timeout=5.0):
        self.urls = urls
        self.timeout = timeout
        self.results = []
        self.mode = CONCURRENCY_MODE

        print(
            f"Detected Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({self.mode})")
        print("=" * 40)

        self.__fastest_url = None

    @property
    def fastest_url(self):
        return self.__fastest_url

    def _parse_url(self, url):
        """Parse URL and return hostname and port."""
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if host.startswith("https://") else 80)
        if not host:
            raise ValueError(f"Invalid URL host: {url}")

        return host, port

    # --- Core Sync Speed Test Function (for Threading/Fallback) ---

    def _test_connection_sync(self, url):
        """Test a single connection speed using synchronous socket."""
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
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            return url, round(latency, 2)
        except Exception:
            return url, MAX_LATENCY
        finally:
            sock.close()

    # --- Async Executor (Asyncio >= 3.8) ---

    async def _test_connection_async(self, url):
        """Test a single connection speed using asyncio."""
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
        """Run all async test tasks concurrently."""
        tasks = [self._test_connection_async(url) for url in self.urls]
        return await asyncio.gather(*tasks)

    # --- Main Execution Logic ---

    def compare_connection_speeds(self):
        """Choose execution mode based on Python version."""

        if self.mode == "unsupported":
            print("Error: Python version is too old (< 2.7 or missing 'futures' dependency for 2.7). Cannot proceed.")
            return

        print(f"--- Starting connection speed test using {self.mode} mode ---")

        if self.mode == "asyncio":
            # Prefer asyncio
            try:
                # asyncio.run exists in 3.7+, but this branch will be enabled only for >=3.8
                self.results = asyncio.run(self._run_async())
            except Exception as e:
                print(f"Asyncio execution failed: {e}. Falling back to Threading.")
                self.results = self._run_sync_executor()

        elif self.mode.startswith("threading"):
            # Use ThreadPoolExecutor (compatible with 2.7 and 3.x)
            self.results = self._run_sync_executor()

        self._report_results()

    def _run_sync_executor(self):
        """Run sync tests using ThreadPoolExecutor."""
        max_workers = min(32, len(self.urls))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._test_connection_sync, url) for url in self.urls]

            results = [future.result() for future in futures]
            return results

    def _report_results(self):
        """Report the final results."""
        if not self.results:
            print("No results were gathered.")
            return

        print("\n--- Speed Test Results Summary ---")

        successful_results = [r for r in self.results if r[1] != MAX_LATENCY]

        if successful_results:
            # Compatible with 2.7 and 3.x min function
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


def set_global_pip_mirror(mirror_url, backup_mirror_url=None):
    """Set pip global mirror and add backup as PyPI."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "config", "set", "global.index-url", mirror_url])
        print(f"Global pip mirror has been successfully set to: {mirror_url}")

        if backup_mirror_url:
            _kv = " ".join(backup_mirror_url)

            subprocess.check_call(
                [sys.executable, "-m", "pip", "config", "set", "global.extra-index-url", _kv.strip()]
            )
            print(f"Backup mirror has been successfully set to: {backup_mirror_url}")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while setting pip mirror: {e}")
        return False

    return True


def reset_pip_mirror():
    """Reset pip configuration to default."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "config", "unset", "global.index-url"])
        subprocess.check_call([sys.executable, "-m", "pip", "config", "unset", "global.extra-index-url"])
        print("pip configuration has been reset to the default settings.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while resetting pip configuration: {e}")
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
        EXTRA_INDEX_URLS.append(DEFAULT_INDEX_URL)
        set_global_pip_mirror(
            mirror_url=tester.fastest_url,
            backup_mirror_url=EXTRA_INDEX_URLS
        )


def entry_point():
    parser = argparse.ArgumentParser(description="A tool to test mirror sources and configure pip.")
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset pip configuration to default settings."
    )
    parser.add_argument(
        "--add-baidu", action="store_true",
        help="(Alpha) Add Baidu paddle mirror."
    )
    parser.add_argument(
        "--add-nvidia", action="store_true",
        help="(Alpha) Add nvidia mirror for rapids.ai"
    )
    args = parser.parse_args()

    if args.reset:
        reset_pip_mirror()
        return

    if args.add_nvidia:
        EXTRA_INDEX_URLS.append("https://pypi.nvidia.com/")
    if args.add_baidu:
        EXTRA_INDEX_URLS.append("https://www.paddlepaddle.org.cn/packages/stable/")

    core_main()


if __name__ == "__main__":
    entry_point()
