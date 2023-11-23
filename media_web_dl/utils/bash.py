import subprocess
import threading
from typing import Callable
from media_web_dl.utils.logger import log


def stream_output(process, handler):
    # 对每一行输出进行处理
    for line in iter(process.readline, b""):
        handler(line)
    process.close()


def run_bash(bash_path_str: str, cleanup: Callable[..., None], *cleanup_args):
    # 使用 subprocess 运行脚本
    process = subprocess.Popen(
        ["bash", bash_path_str], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        # 启动一个线程来处理 stdout
        stdout_thread = threading.Thread(
            target=stream_output,
            args=(
                process.stdout,
                lambda line: print("stdout: " + line.decode().strip()),
            ),
        )
        log.info(
            f"开始运行: {bash_path_str}, 请稍等...\n使用 Ctrl+C 可以终止进程"
        )
        stdout_thread.start()

        # 启动一个线程来处理 stderr
        stderr_thread = threading.Thread(
            target=stream_output,
            args=(
                process.stderr,
                lambda line: print("stderr: " + line.decode().strip()),
            ),
        )
        stderr_thread.start()

        # 等待进程结束
        process.wait()

        # 等待输出线程结束
        stdout_thread.join()
        stderr_thread.join()

    except KeyboardInterrupt:
        # 如果捕获到 KeyboardInterrupt，终止进程
        process.terminate()
        log.info("由于 KeyboardInterrupt, 进程已终止。")
    finally:
        cleanup(*cleanup_args)
        # 无论如何，确保进程已经终止
        process.kill()
