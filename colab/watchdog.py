"""止まった試行の見張り（案A のノートブックのセル 10 が本番と一緒に起動する）。

CaP-X は試行の時間切れを SIGALRM（1000 秒で 1 回だけ）で知らせ、ハンドラが TimeoutError を投げる
（capx/envs/runner.py）。この例外が生成コード自身の `try: ... except Exception:` に捕まると消えてしまい、
生成コードがそのあと終わらないループに入っていると、試行がいつまでも終わらず、そのセルの残りも進まない
（案A の 1 回目の実行の base・handover で 1 回。手で SIGALRM を送り直すと、今度は生成コードの外で
TimeoutError になり、`_exec_user_code` がそのコードの失敗として扱って試行が終わった）。

CaP-X の作業プロセス（multiprocessing の spawn で起きた cap-x の venv の python）が
LIMIT 秒続けて CPU を 80% 超使っていたら SIGALRM を送り直す。ふつうの試行は数分で終わり、試行の合間や
LLM の返事を待つ間は CPU が下がって数え直しになるので、誤って打ち切ることはまずない。
ただし送るのは、そのプロセスが SIGALRM のハンドラを置いているとき（= CaP-X の試行の最中。/proc の SigCgt で見る）だけ。
ハンドラの無い瞬間に送ると、既定の動きでプロセスごと終わって CaP-X の結果待ちが止まるため。
生成コードが毎回 TimeoutError を捕まえる場合は、送り直しても止められない（LIMIT ごとに送り続ける）。
送ったときは標準出力に 1 行書く（セル 10 が logs/watchdog.log に残す）。

  python colab/watchdog.py            # 既定 1200 秒
  WD_LIMIT=900 python colab/watchdog.py
"""

import os
import signal
import time

TICK = 30
LIMIT = int(os.environ.get("WD_LIMIT", "1200"))
HZ = os.sysconf("SC_CLK_TCK")


def workers():
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            cmd = open(f"/proc/{p}/cmdline").read()
        except OSError:
            continue
        if "cap-x/.venv/bin/python" in cmd and "spawn_main" in cmd:
            yield int(p)


def cpu_seconds(pid: int) -> float:
    f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
    return (int(f[11]) + int(f[12])) / HZ   # utime + stime


def has_alarm_handler(pid: int) -> bool:
    """SIGALRM のハンドラが置かれているか（/proc/<pid>/status の SigCgt のビット）。"""
    for line in open(f"/proc/{pid}/status"):
        if line.startswith("SigCgt:"):
            return bool(int(line.split()[1], 16) & (1 << (signal.SIGALRM - 1)))
    return False


def main() -> None:
    last: dict[int, tuple[float, float]] = {}
    streak: dict[int, int] = {}
    fired: dict[int, int] = {}
    print(time.strftime("%Y-%m-%d %H:%M:%S"), f"start (limit {LIMIT}s)", flush=True)
    while True:
        now = time.time()
        alive = set(workers())
        for pid in alive:
            try:
                c = cpu_seconds(pid)
            except OSError:
                continue
            if pid in last:
                busy = (c - last[pid][1]) / (now - last[pid][0]) > 0.8
                streak[pid] = streak.get(pid, 0) + TICK if busy else 0
                if streak[pid] >= LIMIT:
                    try:
                        ready = has_alarm_handler(pid)
                    except OSError:
                        ready = False
                    if ready:
                        os.kill(pid, signal.SIGALRM)
                        fired[pid] = fired.get(pid, 0) + 1
                        print(time.strftime("%Y-%m-%d %H:%M:%S"),
                              f"SIGALRM pid={pid} busy {streak[pid]}s (#{fired[pid]})", flush=True)
                        streak[pid] = 0
                    else:   # 試行の外（ハンドラが無い）。送らずに次の見回りでもう一度見る
                        print(time.strftime("%Y-%m-%d %H:%M:%S"),
                              f"skip pid={pid} busy {streak[pid]}s (no alarm handler)", flush=True)
            last[pid] = (now, c)
        for pid in list(last):   # 終わったプロセスは忘れる（pid の使い回しに備える）
            if pid not in alive:
                last.pop(pid, None)
                streak.pop(pid, None)
        time.sleep(TICK)


if __name__ == "__main__":
    main()
