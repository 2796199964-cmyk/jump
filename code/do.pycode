import subprocess
import time
import sys


def run_pho_cycle():
    while True:
        try:
            print("正在启动 pho_cycle.py...")
            # 运行脚本并等待其完成
            result = subprocess.run([sys.executable, "pho_cycle.py"], check=True)
            print("pho_cycle.py 执行成功。")


        except subprocess.CalledProcessError as e:
            print(f"pho_cycle.py 执行失败，错误信息：{e}")
        except KeyboardInterrupt:
            print("\n正在停止循环...")
            break
        except Exception as e:
            print(f"发生意外错误：{e}")
            # 10 秒后重启
            print("10 秒后重启...")
            time.sleep(10)


if __name__ == "__main__":
    run_pho_cycle()
    # 等待 5 秒
    time.sleep(5)
