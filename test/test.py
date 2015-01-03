import unittest

from tools import *


class TestFunctions(unittest.TestCase):
    def test_get_accused_names(self):
        data = '''
        被　　　告　人 名○○
        xxxx測試失敗xx
        被告人測試失敗
            主 文
        '''

        self.assertEqual(list(get_accused_names(data)), ['人 名○○'])

    def test_extract_table_names(self):
        data = """
            主文
        aaaaaaaaa附表aaaaaaa，附表一二，xxxxxxxxxxx。
            犯罪事實及理由
        """

        self.assertEqual(list(extract_table_names(data)), ['附表', '附表一二'])

    def test_findall_charge_sentence_pairs(self):
        data = \
            '''
            Axx被訴xx部分無罪。
            Axx犯xx罪部分無罪。
            Axx犯xx罪，免刑；
            Axx犯xx罪，處有期徒刑x年x月。
            Axx犯xx罪，處有期徒刑x年x月，減為x年x月，禠奪公權x年。
            Axx犯xx罪，累犯，處有期徒刑x年x月。

            A犯xx罪、xx罪。
            Axxx犯x（x）x、x罪。

            Axx犯xx罪，測試失敗，測試失敗，處有期徒刑x年x月。
            A、B、C均無罪。
            Axxxxx，犯xx罪。

            B犯測試失敗罪。
            '''
        self.assertEqual(list(findall_charge_sentence_pairs('A', data)), [('Axx被訴xx部分無罪', None),
                                                                          ('Axx犯xx罪部分無罪', None),
                                                                          ('A、B、C均無罪', None),
                                                                          ('Axx犯xx罪', '免刑；'),
                                                                          ('Axx犯xx罪', '處有期徒刑x年x月。'),
                                                                          ('Axx犯xx罪', '處有期徒刑x年x月，減為x年x月，禠奪公權x年。'),
                                                                          ('Axx犯xx罪', '累犯，處有期徒刑x年x月。'),
                                                                          ('A犯xx罪、xx罪', None),
                                                                          ('Axxx犯x（x）x、x罪', None),
                                                                          ('Axx犯xx罪', None),
                                                                          ('Axxxxx，犯xx罪', None)])

    def test_extract_all_tables(self):
        data = \
            """
            附表二： blablabla附表三bla,blablab
            ┌─┬────
            └─┴───┘

            附表三： blablablabl
            a,blablabal.
            ┌─┬──────┐
            │X│測試通過│
            ├─┼──┼───┤
            └─┴──────┘

            """
        self.assertEqual(list(extract_all_tables(data)),
                         ['┌─┬────\n└─┴───┘', '┌─┬──────┐\n│X│測試通過│\n├─┼──┼───┤\n└─┴──────┘'])

    def test_extract_rows(self):
        data = \
            """
┌─┬──┬──────┐
│1 │xx│xxxx│
│ 2│xx │xx  │
├─┼───┼────────┤
│ 3│xxx│xxx│
│  ├─────────┼──────┤
│  │xxx │xxxx   │
├─┼────┴─────┼──────┤
│  │444│         │
└─┴────────┴────┘
            """

        self.assertEqual(list(extract_rows(data)),
                         ['│1 │xx│xxxx│\n│ 2│xx │xx  │',
                          '│ 3│xxx│xxx│\n│  ├─────────┼──────┤\n│  │xxx │xxxx   │',
                          '│  │444│         │'])

    def test_parse(self):
        data = ['│1│ │    │',
                '''
                │ 2│測試│ │
                │ 2├─────────┼──────┤
                │  │通過 │測試通過   │''',
                '''
               ││如附表一│A共同犯行使偽造公文書罪，處有期徒刑壹年。如附表二│
               │  │編號14所│所示之偽造印文、署押，（含電池、│
               │  │示     │SIM 卡），均沒收。           │
               ''']

        self.assertEqual(list(parse(data)),
                         [['1', ' ', '    '],
                          [' 2 2  ', '測試─────────通過 ', ' ──────測試通過   '],
                          ['\uf57b    ',
                           '如附表一編號14所示     ',
                           'A共同犯行使偽造公文書罪，處有期徒刑壹年。如附表二所示之偽造印文、署押，（含電池、SIM 卡），均沒收。           ']])


    def test_extract_cells(self):
        data = '''
blabla
附表三：
┌──────────────────────────────────────┐
│98年度離島造林標案核定底價、決標情形一覽表     │
├─┬────┬──────────────────────────┤
│編號  │犯罪事實│主文            │
│   │        ├─────┤
│   │        │    宣告刑       │
├─┼────┼───────────────────────────┤
│一│郭美瑩共同犯行使偽造公文書罪，處有期徒刑壹年壹月；減為有期│
│  │徒刑陸月又拾伍日。│
└─┴────┴───────────────────────┘
blabla

┌───────────────────────┐
│號碼 │交易內容    │總價   │
│    ├────┬──┬────┤     │
│    │品名│單價│數量│ │
└───────────────────┘
'''

        self.assertEqual(list(extract_cells(data,None)),
                         [['98年度離島造林標案核定底價、決標情形一覽表     ',
                           '編號        ',
                           '犯罪事實                ',
                           '主文            ─────    宣告刑       ',
                           '一  ',
                           '郭美瑩共同犯行使偽造公文書罪，處有期徒刑壹年壹月；減為有期徒刑陸月又拾伍日。'],
                             []])


if __name__ == '__main__':
    unittest.main()