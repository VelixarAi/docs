import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/audit_token_evidence.py'
spec = importlib.util.spec_from_file_location('audit', SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = self.root / 'dataset.json'
        self.raw = [dict(question_id=str(i), question_type='synthetic',
                         haystack_dates=['2026-01-01'], haystack_sessions=[[
                             dict(role='user', content='hello')]]) for i in range(120)]
        enc = audit.tiktoken.get_encoding('o200k_base')
        full = len(enc.encode('[Chat session on 2026-01-01]\nuser: hello'))
        self.contexts = [dict(qid=str(i), type='synthetic', context='hello', full_context_tokens=full)
                         for i in range(120)]
        self.answers = [dict(qid=str(i), type='synthetic', reader_prompt_tokens=3,
                             reader_completion_tokens=2, full_context_tokens=full) for i in range(120)]
        self.write()

    def write(self):
        self.dataset.write_text(json.dumps(self.raw))
        for name, rows in [('panel_context.jsonl', self.contexts), ('answers.jsonl', self.answers)]:
            (self.root / name).write_text('\n'.join(json.dumps(row) for row in rows))
        (self.root / 'run.py').write_text('# synthetic harness\n')

    def test_reproduction_includes_dataset_hash_and_full_receipt(self):
        receipt = audit.audit(self.root, self.dataset)
        self.assertIn('dataset', receipt['source_sha256'])
        self.assertEqual(receipt, audit.audit(self.root, self.dataset, expected=receipt))
        self.assertEqual(receipt['all']['totals']['reader_input'], 360)
        receipt['all']['totals']['reader_input'] = 0
        with self.assertRaisesRegex(ValueError, 'Recomputed result'):
            audit.audit(self.root, self.dataset, expected=receipt)

    def test_same_token_length_different_content_cannot_verify(self):
        receipt = audit.audit(self.root, self.dataset)
        self.raw[0]['haystack_sessions'][0][0]['content'] = 'world'
        self.write()
        self.assertEqual(receipt['all'], audit.audit(self.root, self.dataset)['all'])
        with self.assertRaisesRegex(ValueError, 'Source hashes'):
            audit.audit(self.root, self.dataset, expected=receipt)

    def test_history_length_mismatch_rejected_even_under_optimization(self):
        self.raw[0]['haystack_dates'].append('2026-01-02')
        self.write()
        output = self.root / 'output.json'
        result = subprocess.run([sys.executable, '-O', str(SCRIPT), '--artifacts', str(self.root),
                                 '--dataset', str(self.dataset), '--output', str(output)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('History date/session lengths differ', result.stderr)
        self.assertFalse(output.exists())

    def test_duplicate_reader_id_rejected(self):
        self.answers[-1]['qid'] = '0'
        self.write()
        with self.assertRaisesRegex(ValueError, 'unique successful'):
            audit.audit(self.root, self.dataset)

    def test_baseline_mismatch_rejected(self):
        self.contexts[0]['full_context_tokens'] += 1
        self.write()
        with self.assertRaisesRegex(ValueError, 'Recomputed baseline'):
            audit.audit(self.root, self.dataset)


if __name__ == '__main__':
    unittest.main()
