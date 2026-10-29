import unittest
import inspect
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import batch_validation as batch


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.fs = 100
        self.signal = np.zeros(4250)
        self.record = SimpleNamespace(fs=self.fs, sig_name=['MLII'],
                                      p_signal=self.signal[:, None])
        self.annotation = SimpleNamespace(sample=np.array([0, 1999, 2000, 3999, 4000, 4249]),
                                           symbol=['N'] * 6)

    def test_context_clipped_and_center_counted_once(self):
        lengths = []
        def fake_filter(sos, segment):
            lengths.append(len(segment))
            return segment
        # Each extended segment contains annotations represented as peak indices.
        offsets = iter([0, 1700, 3700])
        def fake_peaks(values, **kwargs):
            start = next(offsets)
            points = self.annotation.sample - start
            return points[(points >= 0) & (points < len(values))], {}
        with patch.object(batch.wfdb, 'rdrecord', return_value=self.record), \
             patch.object(batch.wfdb, 'rdann', return_value=self.annotation), \
             patch.object(batch, 'sosfiltfilt', side_effect=fake_filter), \
             patch.object(batch, 'find_peaks', side_effect=fake_peaks):
            out = batch.validate_record_with_context(context_seconds=3)
        self.assertEqual(lengths, [2300, 2550, 550])
        self.assertEqual((out['TP'], out['FP'], out['FN']), (6, 0, 0))

    def test_no_context_is_default(self):
        lengths = []
        def fake_filter(sos, segment):
            lengths.append(len(segment))
            return segment
        with patch.object(batch.wfdb, 'rdrecord', return_value=self.record), \
             patch.object(batch.wfdb, 'rdann', return_value=self.annotation), \
             patch.object(batch, 'sosfiltfilt', side_effect=fake_filter), \
             patch.object(batch, 'find_peaks', return_value=(np.array([], dtype=int), {})):
            batch.validate_record()
        self.assertEqual(lengths, [2000, 2000, 250])

    def test_original_signature(self):
        sig = inspect.signature(batch.validate_record)
        self.assertEqual(str(sig), "(record_id='100', lead_name='MLII', window_seconds=20)")


if __name__ == '__main__':
    unittest.main()
