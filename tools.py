import re
import logging

import pprint
import itertools

pprint = pprint.pprint

log = logging.getLogger(__name__)
# log.setLevel(logging.INFO)

# pattern : no other words in same line
abstract_heading_pattern = r'\n\W*主\s*文\W*\n'
fact_heading_pattern = r'\n\W*事\s*實\W*\n'
reason_heading_pattern = r'\n\W*理\s*由\W*\n'
fact_reason_heading_pattern = r'\n\W*犯罪事實及理由\W*\n'
section_heading_pattern = r'\n\s{4}[\w\s]{2,10}\n'
essay_ending_pattern = r'\W*以上正本證明與原本無異\W*\n'


class PatternNotFoundException(Exception):
    """"""
    pass


def extract_accused_names(fulltext):
    """
    被告名稱抓取

    多人CASE如下沒有考慮：
    被告 人名
        人名
       共兩人

    :return: iterable of name string
    """

    p = r"""
    被\s*告\W+     #被告兩字
    ([\w○\t ]{2,})  #人名公司名,包含mask'○' and space
    \W         #後面不接字
    """

    # locate 主文之前
    start = 0
    end = re.search(abstract_heading_pattern, fulltext).end()
    text = fulltext[start:end]

    matches = re.finditer(p, text, re.VERBOSE)
    return (m.group(1) for m in matches)


def extract_table_names(fulltext):
    """"""

    # locate 主文~事實
    start = re.search(abstract_heading_pattern, fulltext).start()
    # 主文之後的section標題不太一定(eg. 犯罪事實及理由)
    p = '|'.join([fact_heading_pattern, reason_heading_pattern, fact_reason_heading_pattern])
    end = re.search(p, fulltext).end()


    # 提到的附表全包下，非常不精確，有很多提到的附表是跟判刑無關。
    text = re.sub('\n', '', fulltext[start:end])
    matches = re.finditer(r'(附表[零一二三四五六七八九十壹貳參肆伍陸柒捌玖拾]*)', text)
    return (m.group(1) for m in matches)


def findall_charge_sentence_pairs(accused, text):
    """抓罪名和判刑charge+sentence，使用很限制的pattern，charge之後標點符號直接接sentence。
    囧....'禠'!='褫'，同一個字文本內的和自己打的不相等。無法理解？

    失敗case：
    A犯xx罪，xx罪。
    A,B,C 均無罪。
    A犯XX罪，.....，又因..犯..罪，...，又...

    :return: iterable of tuple(charge, declared sentence) of accused
    """
    not_charge_pattern = r'''
    ({0}                #某某某
    [\w、]*無罪\w*)        #接無罪句子允許頓號
    \W                 #標點符號
    '''.format(accused)

    charge_pattern = r'''
    ({0}                     #某某某
    \w*，?                 #允許前面有個句子加逗號，此pattern不多
    \w*犯[\w、（）\(\)]*[^無]罪)        #xxx犯xxx罪句子允許頓號，排除無罪
    \W                      #標點符號
    '''.format(accused)
    # ([^。]*犯[^。]*罪)  #犯罪句子，僅不允許句號在之間，但允許其他符號。這是比較寬鬆的pattern，非常不准。因為table內句子相對簡單，不採用。

    sentence_pattern = r'''
    (
     \w*[，]{0,1}\w*處\w*刑\w*[年月]\w*\W           #處xxxx刑x年x月，
     (
      (\w*減為\w*[年月]\w*\W)    #減刑....。
      |(緩刑\w*\W)
      |(\w*禠奪公權\w*\W)      #禠奪公權x年x月。 三句optional，order任意。
     )*
    )
    '''
    not_sentence_pattern = r'''(免刑\w*\W)'''

    text = re.sub(r'[\n\t ]', '', text)
    ms1 = re.finditer(not_charge_pattern, text, re.VERBOSE)
    not_charges = ((m.group(1), None) for m in ms1)

    # 加一個?允許可以沒有sentence。就是允許沒找到，可能是pattern不符。
    ms2 = re.finditer(charge_pattern + '(' + sentence_pattern + '|' + not_sentence_pattern + ')?', text, re.VERBOSE)
    charge_sentence_pairs = ((m.group(1), m.group(2)) for m in ms2)

    return itertools.chain(not_charges, charge_sentence_pairs)  # not_charge和charge是exclusive pattern


class TableNotFoundException(Exception):
    pass


def extract_all_tables(text):
    """extract all table that has boundary '┌' and '┘'.
    :return:  iterable of table strings.
    """
    tops = re.finditer(r'┌', text)
    bottom_of = lambda top: re.search(r'┘', text[top.start():])
    tables = ( (top, bottom_of(top)) for top in tops )
    return (text[top.start():top.start() + bottom.end()]
            for top, bottom in tables)


def slide2(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def extract_rows(table_text):
    """
    extract rows which are separated by pattern like '├─┼──┴──┴──┤' but '├──┤ ├──┤' or '│ ├──┤ │'.
    :return: iterable of unstructure row of table .
    """

    pattern = r'''
    \n├       #左邊界，需要\n知道換行，因為這裡不是一行一行找的
    [┼┴┬─]+   #中間都是框架符號，不能有字
    ┤\s*?\n    #右邊界
    '''
    start = re.search(r'┐', table_text).start()
    end = re.search(r'└', table_text).end()
    # if not(m1 and m2):
    # raise ValueError("table_text:{} doesn't have ┐ or └ boundary.".format(table_text))
    dividing_lines = re.finditer(pattern, table_text, re.VERBOSE)
    line_starts = (m.start() + 1 for m in dividing_lines)
    dividing_lines_pos = itertools.chain([start], line_starts, [end])  #+1 cuz a \n before ├

    pairs = slide2(dividing_lines_pos)
    rows = (table_text[s:e] for s, e in pairs)
    for row in rows:
        start = row.find('│')
        end = row.rfind('│') + 1
        yield row[start:end]


class TableFormatException(ValueError):
    """ not expected table structure"""
    pass


def parse(rows):
    """
    structure the string of multiline row to one line for readability.
    parse to readable cells of rows: ['cell1','cell2',cells,...],[...],rows...
    columns數每一行要求一樣。

    無法handle這種case：
│號碼 │交易內容    │總價   │
│    ├────┬──┬────┤      │
│    │品名│單價│數量│      │
    可以作但是比較麻煩。

    :return: iterable of str list; the str list is a row and the str is a cell.
    """
    pattern = r'[│├┤┼]'
    for multiline_row in rows:
        lines = multiline_row.strip().split('\n')

        # requirement checking
        # columns數每一行要求一樣
        column_lens = (len(re.findall(pattern, line)) for line in lines)
        column_len = next(column_lens)
        if not all(l == column_len for l in column_lens):
            raise TableFormatException('the column is not fixed :{}...'.format(multiline_row[:15]))

        result = [''] * column_len
        for line in lines:
            columns = (e for e in re.split(pattern, line.strip()) if e != '')
            result = map(''.join, zip(result, columns))

        yield list(result)


def extract_cells(fulltext, fname):
    """抓出所有table，並parse into readable cells of table。
    輸出cells list per table,
    無法解析的table輸出[]
    :return: list of table which is composed of a list of cell strings ,
    :rtype : list[list[str]]
    """
    appendix = fulltext
    readable_cells_per_table = []
    format_exception = []
    for table in extract_all_tables(appendix):
        try:
            readable_rows = parse(extract_rows(table))
            cells = [cell_str for row in readable_rows for cell_str in row]
            readable_cells_per_table.append(cells)
        except TableFormatException as e:
            readable_cells_per_table.append([])
            format_exception.append(e)
            continue

    # logging TableFormatException for debugging
    if format_exception:
        log.info('\n表格parsing失敗;{0} has table format not expected.'.format(fname))
        for e in format_exception:
            log.debug('{}'.format(e))

    return readable_cells_per_table


#
# def extract_table(name, text):
# '''
# find many matching of tableheader e.g.'附表X' and,
# find the following table boundary '┌' and
# validate that the boundary is for the tableX .
# return table position (start,end) in text.
# '''
#
#     def find_valid_table(text):
#         '''return the best table match
#          'validate' the condition : distance<100
#         '''
#         # the pattern of tableheader is -- no words at left side of the name until \n.
#         header_pattern = r'\n[^\w\n]*?{0}'.format(name)
#         header_matches = tuple(re.finditer(header_pattern, text))
#         table_matches = tuple(re.finditer(r'┌', text))
#
#         DIST_TRESHOLD = 100
#
#         candidates = []
#         for table, header in itertools.product(table_matches, header_matches):
#             dist = table.start() - header.start()
#             candidates.append((table, dist))
#
#         candidates = [cand for cand in candidates if 0 <= cand[1] < DIST_TRESHOLD]
#         if not candidates:
#             raise TableNotFoundException(
#                 'Valid table:{0} not found. \n\t candidates=None ; header_matches={1}; #table_matches={2}.\n'
#                 .format(name, [m.group() for m in header_matches], len(table_matches)))
#
#         best = min(candidates, key=operator.itemgetter(1))
#         return best[0]
#
#
#     table = find_valid_table(text)
#     bottom = re.search('┘', text[table.start():])
#     start, end = (table.start(), table.start() + bottom.end())
#     return text[start:end]
