"""Reproduce one frozen benchmark audit without publishing conversation text."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

import tiktoken


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def aggregate(rows):
    sums = {key: sum(row[key] for row in rows) for key in (
        'baseline_context', 'retrieved_context', 'reader_input', 'reader_output')}
    require(sums['baseline_context'] > 0, 'Baseline must be positive')
    return dict(n=len(rows), totals=sums,
                means={key: value / len(rows) for key, value in sums.items()},
                context_reduction_pct=100 * (1 - sums['retrieved_context'] / sums['baseline_context']),
                input_vs_context_reference_pct=100 * (1 - sums['reader_input'] / sums['baseline_context']))


def audit(root, dataset, *, expected=None):
    sources = {name: root / name for name in ('panel_context.jsonl', 'answers.jsonl', 'run.py')}
    sources['dataset'] = dataset
    # Snapshot the bytes once: provenance and parsing must refer to the same input.
    blobs = {name: path.read_bytes() for name, path in sources.items()}
    hashes = {name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()}
    if expected is not None:
        require(hashes == expected['source_sha256'], 'Source hashes differ from expected receipt')
        require(expected['tokenizer'] == 'o200k_base' and
                expected['tiktoken_version'] == tiktoken.__version__, 'Tokenizer differs from expected receipt')
    decode_rows = lambda name: [json.loads(line) for line in blobs[name].decode().splitlines() if line.strip()]
    contexts, answers = decode_rows('panel_context.jsonl'), decode_rows('answers.jsonl')
    raw = json.loads(blobs['dataset'])
    questions = {row['question_id']: row for row in raw}
    require(len(questions) == len(raw), 'Duplicate dataset question IDs')
    successful = [row for row in answers if 'reader_prompt_tokens' in row]
    by_id = {row['qid']: row for row in successful}
    require(len(successful) == len(by_id) == 120, 'Expected 120 unique successful reader records')
    require(len(contexts) == len({row['qid'] for row in contexts}) == 120,
            'Expected 120 unique context records')
    require(set(by_id) == {row['qid'] for row in contexts}, 'Context and reader IDs differ')
    require(all('reader_prompt_tokens' in row or 'error' in row for row in answers),
            'Answer record has neither usage nor explicit error')
    enc = tiktoken.get_encoding('o200k_base')
    rows = []
    for context in contexts:
        qid = context['qid']
        question, answer = questions[qid], by_id[qid]
        require(len(question['haystack_dates']) == len(question['haystack_sessions']),
                'History date/session lengths differ')
        baseline = sum(len(enc.encode('\n'.join(
            [f'[Chat session on {date}]'] +
            [f"{turn.get('role', '?')}: {turn.get('content', '')}" for turn in turns])))
            for date, turns in zip(question['haystack_dates'], question['haystack_sessions']))
        require(baseline == context['full_context_tokens'] == answer['full_context_tokens'],
                'Recomputed baseline differs from saved counts')
        for key in ('reader_prompt_tokens', 'reader_completion_tokens'):
            require(type(answer[key]) is int and answer[key] >= 0, 'Invalid reader token count')
        require(answer['type'] == context['type'] == question['question_type'], 'Question type differs')
        rows.append(dict(task_type=context['type'], baseline_context=baseline,
                         retrieved_context=len(enc.encode(context['context'])),
                         reader_input=answer['reader_prompt_tokens'],
                         reader_output=answer['reader_completion_tokens']))
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row['task_type']].append(row)
    result = dict(audited_at='2026-09-27', tokenizer='o200k_base', tiktoken_version=tiktoken.__version__,
                  source_sha256=hashes, all=aggregate(rows),
                  by_task={key: aggregate(value) for key, value in sorted(groups.items())},
                  failed_records_excluded=len(answers) - len(successful), limitations=[
        'Baseline tokenized stored history, not an executed full-context provider arm.',
        'Reader input includes prompt framing; baseline context does not.',
        'Source harness filters retrieved hits by question scope.',
        'No cached-input split, retry spend, ingestion spend or baseline output usage.',
        'Published 16274 context mean is not reproduced by present panel_context.jsonl; current recomputation is 16308.6583.',
        'No matched-quality or invoice-saving claim.'])
    if expected is not None:
        require(result == expected, 'Recomputed result differs from expected receipt')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    expected = json.loads(args.verify_against.read_text()) if args.verify_against else None
    result = audit(args.artifacts, args.dataset, expected=expected)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified receipt written.' if expected is not None else 'Audit receipt written.')


if __name__ == '__main__':
    main()
