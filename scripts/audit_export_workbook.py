"""Read-only OOXML audit; preserve source cells and never fill missing months."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workbook', required=True)
parser.add_argument('--output-dir', default='data')
args = parser.parse_args()
SOURCE = Path(args.workbook)
OUT = Path(args.output_dir)
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
records, summaries = [], []
with ZipFile(SOURCE) as book:
    strings = []
    if 'xl/sharedStrings.xml' in book.namelist():
        strings = [''.join(n.itertext()) for n in ET.fromstring(book.read('xl/sharedStrings.xml'))]
    workbook = ET.fromstring(book.read('xl/workbook.xml'))
    rels = {n.attrib['Id']: n.attrib['Target'] for n in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
    for sheet in workbook.find('s:sheets', NS):
        name = sheet.attrib['name']
        target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        xml = ET.fromstring(book.read(target))
        cells = {}
        for cell in xml.findall('.//s:sheetData/s:row/s:c', NS):
            v = cell.find('s:v', NS)
            text = v.text if v is not None else ''
            if cell.attrib.get('t') == 's':
                text = strings[int(text)]
            elif cell.attrib.get('t') == 'inlineStr':
                text = ''.join(cell.find('s:is', NS).itertext())
            cells[cell.attrib['r']] = {'value': text or '', 'formula': cell.findtext('s:f', default='', namespaces=NS)}
        year_rows = []
        for address, cell in cells.items():
            value = cell['value']
            if not address.startswith('A') or not re.fullmatch(r'20\d{2}(0[1-9]|1[0-2])', value):
                continue
            row = address[1:]
            values = [cells.get(c+row, {}).get('value', '') for c in 'BCD']
            if not all(values):
                raise ValueError(f'Incomplete numeric observation: {name}!{address}')
            month = value[:4]+'-'+value[4:]
            assert value[:4] in name, (name, month)
            record = dict(month=month, fob_usd=values[0], net_weight_kg=values[1], records=values[2],
                          destination='World', source_ref=f'workbook-sha256:{digest}#{name}!A{row}:D{row}',
                          source_sheet=name, source_range=f'A{row}:D{row}', release_date='', vintage_date='')
            for field in ['fob_usd', 'net_weight_kg', 'records']:
                assert Decimal(record[field]) > 0, record
            records.append(record)
            year_rows.append(record)
        totals = []
        for address, cell in cells.items():
            if 'TOTAL' in cell['value'].upper() and address.startswith('A'):
                row = address[1:]
                detail = {'label_cell': address, 'label': cell['value'], 'columns': {}}
                for col, field in zip('BCD', ['fob_usd', 'net_weight_kg', 'records']):
                    reported = cells.get(col+row, {})
                    if not reported.get('value'):
                        continue
                    total = sum(Decimal(r[field]) for r in year_rows)
                    delta = Decimal(reported['value'])-total
                    detail['columns'][field] = dict(cell=col+row, cached_value=reported['value'], formula=reported['formula'],
                                                   monthly_sum=str(total), cached_minus_monthly_sum=str(delta),
                                                   agrees_within_001=abs(delta) <= Decimal('.01'))
                totals.append(detail)
        summaries.append(dict(sheet=name, observations=len(year_rows), headers={c: cells.get(c, {}).get('value') for c in ['A4', 'B4', 'C4', 'D4']}, totals=totals))
records.sort(key=lambda r:r['month'])
assert len({r['month'] for r in records}) == len(records)
first, last = records[0]['month'], records[-1]['month']
calendar = [f'{year}-{month:02}' for year in range(int(first[:4]), int(last[:4])+1) for month in range(1,13) if first <= f'{year}-{month:02}' <= last]
audit = dict(source_filename=SOURCE.name, workbook_sha256=digest, source_status='Researcher-supplied workbook; publisher and historical vintages not independently authenticated',
             observed_months=len(records), first_month=first, last_month=last, missing_calendar_months=sorted(set(calendar)-{r['month'] for r in records}),
             destination_breakdown=False, release_dates_provided=False, historical_vintages_provided=False,
             measures={'fob_usd':'FOB US$ (nominal)', 'net_weight_kg':'PESO NETO KGM', 'records':'REGISTROS'},
             sheets=summaries, note='Workbook title ENERO DICIEMBRE does not establish twelve observed months; only populated YYYYMM rows are extracted. No raw workbook or personal document metadata is published.')
OUT.mkdir(parents=True, exist_ok=True)
with (OUT/'exports_monthly_supplied.csv').open('w', encoding='utf8', newline='') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
(OUT/'exports_source_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({k:v for k,v in audit.items() if k != 'sheets'}, ensure_ascii=False, indent=2))
print(json.dumps({'annual_total_discrepancies': [s for s in summaries if any(not c['agrees_within_001'] for t in s['totals'] for c in t['columns'].values())]}, ensure_ascii=False, indent=2))
