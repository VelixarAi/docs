import json, hashlib, statistics, pathlib, collections
import tiktoken
import argparse
parser=argparse.ArgumentParser(description="Reconcile local benchmark artifacts without publishing conversation text")
parser.add_argument("--artifacts",type=pathlib.Path,required=True)
parser.add_argument("--dataset",type=pathlib.Path,required=True)
parser.add_argument("--output",type=pathlib.Path,required=True)
args=parser.parse_args()
root=args.artifacts
enc=tiktoken.get_encoding('o200k_base')
load=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
ctx=load(root/'panel_context.jsonl'); answers=load(root/'answers.jsonl')
raw=json.loads(args.dataset.read_text())
questions={r['question_id']:r for r in raw}
def full(q):
 return sum(len(enc.encode('\n'.join([f'[Chat session on {date}]']+[f"{t.get('role','?')}: {t.get('content','')}" for t in turns]))) for date,turns in zip(q['haystack_dates'],q['haystack_sessions']))
byid={r['qid']:r for r in answers if 'reader_prompt_tokens' in r}
assert len(byid)==120
assert len(ctx)==120 and len({r['qid'] for r in ctx})==120
assert len([r for r in answers if 'reader_prompt_tokens' in r])==120
rows=[]
for r in ctx:
 b=full(questions[r['qid']]); assert b==r['full_context_tokens']
 a=byid[r['qid']]; assert a['full_context_tokens']==b
 rows.append(dict(task_type=r['type'],baseline_context=b,retrieved_context=len(enc.encode(r['context'])),reader_input=a['reader_prompt_tokens'],reader_output=a['reader_completion_tokens']))
def aggregate(rs):
 sums={k:sum(r[k] for r in rs) for k in ['baseline_context','retrieved_context','reader_input','reader_output']}
 return dict(n=len(rs),totals=sums,means={k:v/len(rs) for k,v in sums.items()},context_reduction_pct=100*(1-sums['retrieved_context']/sums['baseline_context']),input_vs_context_reference_pct=100*(1-sums['reader_input']/sums['baseline_context']))
groups=collections.defaultdict(list)
for r in rows: groups[r['task_type']].append(r)
result=dict(audited_at='2026-09-27',tokenizer='o200k_base',tiktoken_version=tiktoken.__version__,source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in ['panel_context.jsonl','answers.jsonl','run.py']},all=aggregate(rows),by_task={k:aggregate(v) for k,v in sorted(groups.items())},failed_records_excluded=len(answers)-len(byid),limitations=['Baseline tokenized stored history, not an executed full-context provider arm.','Reader input includes prompt framing; baseline context does not.','Source harness filters retrieved hits by question scope.','No cached-input split, retry spend, ingestion spend or baseline output usage.','Published 16274 context mean is not reproduced by present panel_context.jsonl; current recomputation is 16308.6583.','No matched-quality or invoice-saving claim.'])
out=args.output;out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
