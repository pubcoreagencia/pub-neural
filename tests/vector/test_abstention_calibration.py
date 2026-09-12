import unittest

from scripts.calibrate_abstention_v0_3 import calibrate


class TestAbstentionCalibration(unittest.TestCase):
    def test_threshold_selection_uses_calibration_only(self):
        records = [
            {
                "query_id": "QRY-01",
                "evaluation_split": "CALIBRATION",
                "query_type": "SUPPORTED",
                "dense_top1_similarity": 0.95,
            },
            {
                "query_id": "QRY-02",
                "evaluation_split": "CALIBRATION",
                "query_type": "Q13_UNSUPPORTED",
                "dense_top1_similarity": 0.70,
            },
            {
                "query_id": "QRY-03",
                "evaluation_split": "HOLDOUT",
                "query_type": "SUPPORTED",
                "dense_top1_similarity": 0.99,
            },
        ]

        result = calibrate(records)

        self.assertFalse(result["holdout_used_for_selection"])
        self.assertEqual(result["selection_split"], "CALIBRATION")
        self.assertGreaterEqual(result["selected_threshold"], 0.70)
        self.assertLessEqual(result["selected_threshold"], 0.95)

    def test_duplicate_query_across_splits_is_rejected(self):
        records = [
            {
                "query_id": "QRY-01",
                "evaluation_split": "CALIBRATION",
                "query_type": "SUPPORTED",
                "dense_top1_similarity": 0.95,
            },
            {
                "query_id": "QRY-01",
                "evaluation_split": "HOLDOUT",
                "query_type": "SUPPORTED",
                "dense_top1_similarity": 0.96,
            },
        ]

        with self.assertRaises(ValueError):
            calibrate(records)

    def test_invalid_similarity_is_rejected(self):
        records = [
            {
                "query_id": "QRY-01",
                "evaluation_split": "CALIBRATION",
                "query_type": "SUPPORTED",
                "dense_top1_similarity": 1.1,
            }
        ]

        with self.assertRaises(ValueError):
            calibrate(records)


if __name__ == "__main__":
    unittest.main()
