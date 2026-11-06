import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from run_artifacts import new_run, complete

class ArtifactTests(unittest.TestCase):
    def test_missing_and_duplicate_execution_fail(self):
        for records in [[{'name':'a','passed':True}],[{'name':'a','passed':True},{'name':'a','passed':True}]]:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);(root/'data').mkdir();(root/'data/knowledge.json').write_text('[]')
                out=new_run(root,'http',['a','b'],['a','b'])
                self.assertFalse(complete(out,records))
    def test_complete_selection(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'data').mkdir();(root/'data/knowledge.json').write_text('[]')
            out=new_run(root,'http',['a'],['a'])
            self.assertTrue(complete(out,[{'name':'a','passed':True}]))
