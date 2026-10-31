"""誤差ありの条件で、生成コードが「位置を何度も読んで平均・中央値をとる」書き方かを数える（自動の目安。正規表現なので取りこぼしがありうる）。

  python3 scripts/scan_averaging.py
"""
import re,glob,os,sys
from pathlib import Path
TR=re.compile(r"trial_(\d+)_sandboxrc_(-?\d+)_reward_([-\d.]+)_taskcompleted_(\d)")
def final_dirs(pattern):
    best={}
    for d in glob.glob(pattern+'/trial_*'):
        m=TR.search(os.path.basename(d)); k=int(m.group(1))
        if k not in best or os.path.getmtime(d)>os.path.getmtime(best[k][0]): best[k]=(d,int(m.group(4)))
    return list(best.values())
def kind(code):
    reads=len(re.findall(r"get_\w*pose\(", code))
    loop_read=bool(re.search(r"for [^\n]*:\s*\n(?:[ \t]+[^\n]*\n){0,6}?[ \t]+[^\n]*get_\w*pose\(", code))
    stat=bool(re.search(r"np\.(mean|median|average)\(", code))
    rng=bool(re.search(r"range\(\s*\w+", code))
    return stat and rng and reads>=1
sources={'main':['claude-cli__claude-haiku-5-5@medium','claude-cli__claude-opus-5-5@medium','agy-cli__gemini-3.8-flash-medium','agy-cli__gemini-4-argon-medium','agy-cli__gpt-oss-120b-medium'],
 'clean':['codex-cli__gpt-6.1-terra@medium','codex-cli__gpt-6.1-sol@medium','codex-cli__gpt-6-astra@medium','replay-cli__claude-fable-5-1@medium']}
print(f"{'model':36s} {'cell':12s} 平均化  成功(平均化あり) 成功(なし)")
for tag,models in sources.items():
  for m in models:
    for cond in ['base','noisy','noisy_mt']:
      for task in ['stack','nut']:
        rows=[]
        for d,ok in final_dirs(f"runs/{tag}/{cond}/{m}/*/{task}"):
            p=Path(d)/'code.py'; rows.append((kind(p.read_text()) if p.exists() else False, ok))
        if not rows: continue
        a=[ok for av,ok in rows if av]; n=[ok for av,ok in rows if not av]
        print(f"{m.split('__')[1]:36s} {cond+'/'+task:12s} {len(a):2d}/{len(rows)}   {sum(a)}/{len(a)}            {sum(n)}/{len(n)}")
