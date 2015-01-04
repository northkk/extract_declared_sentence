import logging
import logging.config
import itertools
import os
import pprint
import json
import sys

import tools


logging.basicConfig(filename='extract_declared_sentence.log', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)

count = {'doc': 0,  # #docs processed
         'accused_extraction_fail': 0,
         'table': 0,  # #tables processed
         'table_format_exception': 0,
         'table_processing_fail': 0,  # include format exception count
         'output': 0  # #docs that has had result written out.
}


def main(extract_accuseds=tools.extract_accuseds,
         extract_sentences=tools.extract_sentences):
    """
    output [file name,{accused:[(charge,sentences),...],...}],... as json.
    you can provide custom functions to keyword args extract_accuseds(text) and extract_accuseds(name,text)."""
    DIR = sys.argv[1]
    if os.path.isdir(DIR):
        dn, _, fns = next(os.walk(DIR))
        paths = (os.path.join(dn, fn) for fn in fns if not fn.startswith('.'))
    elif os.path.isfile(DIR):
        paths = [DIR]
    else:
        print('only accept a file or a dir path')
        return


    for path in paths:
        count['doc'] += 1
        with open(path) as f:
            text = f.read()

            # #被告抽取
            try:
                accused_list = frozenset(extract_accuseds(text))
                if not accused_list:
                    raise Exception('PatternNotFound: the return of accused name is None.')

            except Exception as e:
                log.exception('\n{}被告抽取失敗。'.format(f.name))
                count['accused_extraction_fail'] += 1
                continue

            # #附表罪名和宣告刑抽取
            try:
                # 不做主文附表名稱抽取，直接table全抓。
                # 假設附表一定是表格
                cells_per_table = tools.extract_cells(text)

                #count
                failed_count = sum(1 for cells in cells_per_table if not cells)
                if failed_count:
                    log.info('\n表格parsing失敗;{0} has table format not expected.'.format(f.name))
                    count['table_format_exception'] += failed_count
                    count['table_processing_fail'] += failed_count
                count['table'] += len(cells_per_table)

                # 每個人的charge
                # 假設罪名和宣告刑會放在同一cell，
                charge_sentence_pairs = {}
                for accused in accused_list:
                    charge_sentence_pairs[accused] = []
                    for cell in itertools.chain.from_iterable(cells_per_table):
                        charge_sentence_pairs[accused] += list(extract_sentences(accused, cell))

            except Exception as e:
                log.exception('\n{}表格內宣告刑抽取失敗'.format(f.name))
                count['table_processing_fail'] += 1
                continue
            else:
                if any(charge_sentence_pairs.values()):  # 有東西才輸出
                    filename = os.path.basename(f.name)
                    count['output'] += 1
                    yield [filename, charge_sentence_pairs]
                else:
                    pass


if __name__ == "__main__":
    for res in main():
        res_json = json.dumps(res, indent=5, ensure_ascii=False)
        print(res_json)
        # pprint.pprint(res)

    print('統計：')
    pprint.pprint(count)
