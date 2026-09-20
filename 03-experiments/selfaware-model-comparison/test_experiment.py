import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from run_experiment import Ledger, sample_data
import numpy as np
from analyze_results import measures


class ExperimentTests(unittest.TestCase):
    def test_metrics_capture_false_abstention_and_missed_uncertainty(self):
        labels = np.array([True, True, False, False])
        uncertain = np.array([[True, False, True, False]])
        correct = np.array([[False, True, False, False]])
        self.assertTrue(np.allclose(measures(uncertain, correct, labels), [[.5,.5,.5,.5,.5]]))
        self.assertEqual(measures(np.zeros_like(uncertain),correct,labels)[0,0],0)

    def test_concurrent_reservations_cannot_overspend(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Ledger(Path(d)/'ledger.json', 1)
            def reserve(_):
                try: return ledger.reserve(.3, 'test')
                except RuntimeError: return None
            with ThreadPoolExecutor(8) as pool:
                results = list(pool.map(reserve, range(20)))
            self.assertEqual(sum(x is not None for x in results), 3)
            self.assertAlmostEqual(ledger.total(), .9)
            self.assertAlmostEqual(Ledger(ledger.path, 1).total(), .9)
            ledger.settle(0, .1)
            self.assertAlmostEqual(ledger.total(), .7)

    def test_unknown_cost_is_not_refunded(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Ledger(Path(d)/'ledger.json', 1)
            ledger.reserve(.4, 'test')
            with self.assertRaises(RuntimeError): ledger.settle(0, None)
            self.assertEqual(ledger.total(), .4)
            with self.assertRaises(RuntimeError): ledger.settle(0, .5)
            self.assertEqual(ledger.total(), .5)

    def test_sample_balanced_reproducible_unique(self):
        config = json.loads((Path(__file__).parent/'config-original.json').read_text())
        data = json.loads((Path(config['selfaware_root'])/'data/SelfAware.json').read_text(encoding='utf-8'))['example']
        rows = sample_data(data)
        self.assertEqual(rows, sample_data(data))
        self.assertEqual(len({r['question_id'] for r in rows}), 750)
        self.assertEqual(sum(r['answerable'] for r in rows), 520)
        self.assertEqual([r['answerable'] for r in rows[:2]], [True, False])


if __name__ == '__main__': unittest.main()
