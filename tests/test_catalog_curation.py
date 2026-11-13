import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from catalog_curation import text_words


class CurationTests(unittest.TestCase):
    def test_literal_quotes_do_not_merge_tsv_rows(self):
        tsv='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
        tsv+='5\t1\t1\t1\t1\t1\t10\t20\t5\t5\t20\t"\n'
        tsv+='5\t1\t1\t1\t1\t2\t30\t20\t100\t20\t90\tWATERMARK\n'
        words=text_words(tsv)
        self.assertEqual([w['text'] for w in words],['WATERMARK'])
        self.assertEqual(words[0]['box'],[30,20,100,20])


if __name__=='__main__':
    unittest.main()
