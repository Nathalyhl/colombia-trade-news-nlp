import argparse
import hashlib
import json
from pathlib import Path
import sys
from importlib.metadata import version

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from trade_news.articles import read_jsonl
from trade_news.economics import audit_trade, compare, lead_lag, load_trade, news_features

parser = argparse.ArgumentParser(description='Reproduce explicitly assumed-timing retrospective scenarios, not real-time forecasts')
parser.add_argument('--data-dir', default='data')
args = parser.parse_args()
directory = Path(args.data_dir)
output = directory
trade_path = output/'exports_monthly_supplied.csv'
trade = load_trade(trade_path)
rows = read_jsonl(directory/'headlines.jsonl')
scores = read_jsonl(directory/'contextual_scores.jsonl')
months = [r['month'] for r in json.loads((directory/'collection_log.json').read_text('utf8'))['requests']]
reports = {}
for name, lag, excluded, domains in [('main_assumed_lag_2', 2, False, None), ('assumed_lag_1', 1, False, None),
    ('assumed_lag_3', 3, False, None), ('exclude_reporting', 2, True, None),
    ('valora_only', 2, False, ['valoraanalitik.com']), ('larepublica_only', 2, False, ['larepublica.co'])]:
    features = news_features(rows, scores, months, excluded, domains)
    report = compare(trade, features, allow_revised_history=True, assumed_release_lag=lag)
    report['reporting_candidates_excluded'] = excluded
    report['fixed_press_domains'] = domains
    report['lead_lag'] = lead_lag(trade, features)
    reports[name] = report
    (output/f'economic_{name}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')
    print(json.dumps({'scenario': name, 'status': report['status'], 'metrics': report['metrics'], 'skipped': report['skipped']}, ensure_ascii=False), flush=True)
report = dict(status='executed_retrospective_scenarios_not_real_time', trade_audit=audit_trade(trade),
    runtime={name: version(name) for name in ['pandas', 'statsmodels', 'numpy', 'scipy']},
    input_sha256=hashlib.sha256(trade_path.read_bytes()).hexdigest(),
    features_sha256=hashlib.sha256((directory/'headlines.jsonl').read_bytes()).hexdigest(),
    contextual_scores_sha256=hashlib.sha256((directory/'contextual_scores.jsonl').read_bytes()).hexdigest(),
    protocol_sha256=hashlib.sha256((PROJECT/'docs/STUDY_PROTOCOL_ES.md').read_bytes()).hexdigest(),
    primary_scenario='main_assumed_lag_2', scenarios=reports,
    human_validation_status='No adjudicated independent labels; classification accuracy unmeasured',
    source_status='Researcher-supplied workbook. Numerical series is not independently authenticated as the official certified DANE series.',
    limitations=['Assumed publication timing, current revised numerical history, retrospectively retrieved articles and fixed language model.',
        'Twelve requested test origins, common successful folds only; inspect sample size and failed fits.',
        'Source and reporting-role sensitivities are diagnostic; no best model is selected from test errors.'])
(output/'economic_evaluation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')
