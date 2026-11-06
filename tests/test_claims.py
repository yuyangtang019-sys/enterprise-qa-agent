import copy
import unittest
from test_agent import DATA
from enterprise_qa.knowledge import Knowledge
from enterprise_qa.claims import render, facts

class ClaimsTests(unittest.TestCase):
    def setUp(self):
        self.k=Knowledge(DATA); self.e=self.k.execute({'action':'read','document_id':'TRAVEL-NEW','fragment_id':'p1'})
        self.ev={('TRAVEL-NEW','p1'):self.e}
        self.c={'citation_id':'C1','document_id':'TRAVEL-NEW','fragment_id':'p1','version':self.e['document']['version'],'quote':self.e['text']}
        self.a={'answer':'','outcome':'answered','citations':[self.c],'gaps':[],'claims':[{'type':'quote','citation_id':'C1'}]}
    def test_quote_is_rendered_not_model_prose(self):
        text,_,_=render(self.a,self.ev,self.k.digest); self.assertIn('上海住宿上限每晚600元',text)
        self.a['answer']='上海650元北京600元'
        with self.assertRaises(ValueError): render(self.a,self.ev,self.k.digest)
    def test_negation_cut_rejected(self):
        self.e['text']='不允许报销。';self.c['quote']='允许报销。'
        with self.assertRaises(ValueError): render(self.a,self.ev,self.k.digest)
    def test_replacement_direction(self):
        self.a['claims']=[{'type':'replacement','citation_id':'C1','source_document_id':'TRAVEL-OLD','target_document_id':'TRAVEL-NEW'}]
        with self.assertRaises(ValueError): render(self.a,self.ev,self.k.digest)
    def test_replacement_negative(self):
        self.e['text']='本制度不替代 TRAVEL-OLD。';self.c['quote']=self.e['text']
        self.a['claims']=[{'type':'replacement','citation_id':'C1','source_document_id':'TRAVEL-NEW','target_document_id':'TRAVEL-OLD'}]
        with self.assertRaises(ValueError): render(self.a,self.ev,self.k.digest)
    def test_signed_arithmetic(self):
        fs=facts(self.e); c={'type':'arithmetic','operation':'difference','left_fact_id':fs[0]['fact_id'],'right_fact_id':fs[1]['fact_id'],'expected_value':'-50'}
        self.a['claims'].append(c);self.assertEqual(render(self.a,self.ev,self.k.digest)[2][0]['amount'],'-50')
        c['expected_value']='50'
        with self.assertRaises(ValueError): render(self.a,self.ev,self.k.digest)
    def test_equal_values_distinct_facts(self):
        self.e['text']=self.e['text'].replace('650','600');self.c['quote']=self.e['text'];fs=facts(self.e)
        self.a['claims'].append({'type':'arithmetic','operation':'sum','left_fact_id':fs[0]['fact_id'],'right_fact_id':fs[1]['fact_id'],'expected_value':'1200'})
        self.assertEqual(render(self.a,self.ev,self.k.digest)[2][0]['amount'],'1200')
    def test_pagination(self):
        o=self.k.execute({'action':'search','query':'制度'});self.assertIn('has_more',o); self.assertIn('total_candidates',o)

    def test_gap_unknown_rejected(self):
        self.a['gaps']=['unsupported_free_text']
        with self.assertRaises(KeyError): render(self.a,self.ev,self.k.digest)
    def test_missing_operand_rejected(self):
        self.a['claims'].append({'type':'arithmetic','operation':'sum','left_fact_id':'absent','right_fact_id':'absent','expected_value':'1200'})
        with self.assertRaises(KeyError): render(self.a,self.ev,self.k.digest)
    def test_zero_difference_distinct_sources(self):
        self.e['text']=self.e['text'].replace('650','600');self.c['quote']=self.e['text']; fs=facts(self.e)
        self.a['claims'].append({'type':'arithmetic','operation':'difference','left_fact_id':fs[0]['fact_id'],'right_fact_id':fs[1]['fact_id'],'expected_value':'0'})
        self.assertEqual(render(self.a,self.ev,self.k.digest)[2][0]['amount'],'0')

if __name__=='__main__': unittest.main()
