"""Compare methods on the same local record 100, independent of cwd."""
import argparse
import json
from pathlib import Path
from batch_validation import validate_record_with_context

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', nargs='?', default=str(Path(__file__).resolve().parent / '100'))
    record = parser.parse_args().record
    print(json.dumps({
        'baseline': validate_record_with_context(record, 'MLII', context_seconds=0, pn_dir=None),
        'context_3s': validate_record_with_context(record, 'MLII', context_seconds=3, pn_dir=None),
    }, indent=2, allow_nan=False))
