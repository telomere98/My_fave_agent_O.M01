import sys
from bert_evaluator import BertEvaluator
import MeCab
import aiml
tagger = MeCab.Tagger('-Owakati -r /etc/mecabrc')
tagger.parse("")

class DialogueSystemBert:
    def __init__(self):
        from elasticsearch import Elasticsearch
        self.es = Elasticsearch("http://localhost:9200")
        self.evaluator = BertEvaluator()
        self.tagger = MeCab.Tagger('-Owakati -r /etc/mecabrc')

    def aiml_init(self, input):
        sessionId = input['sessionId']
        # AIMLを読み込むためのインスタンスを用意
        kernel = aiml.Kernel()
        # aiml.xmlを読み込む
        kernel.learn("/home/x19069/O.M01/aiml.xml")
        # セッションごとに保存する
        self.sessiondic[sessionId] = kernel
        print('aiml_initialize...', flush = True)
    
    def aiml_reply(self, input):
        sessionId = input['sessionId']
        utt = input['utt']
        utt = self.tagger.parse(utt)
        # 対応するセッションのkernelを取り出し，respondでマッチするルールを探す
        response = self.sessiondic[sessionId].respond(utt)
        print(sessionId, utt, response)
        return {'utt': response, 'end':False}    

    def ebdm_reply(self, input):
        max_score = .0
        result = ''

        for r in self.__reply(input['utt']):
            score = self.evaluate(input['utt'], r)
            if score >= max_score:
                max_score = score
                result = r[1]
        return {"utt": result, "end": False}


    def ebdm_reply_nega(self, input):
        max_score = .0
        result = ''

        for r in self.__reply_nega(input['utt']):
            score = self.evaluate(input['utt'], r)
            if score >= max_score:
                max_score = score
                result = r[1]
        return {"utt": result, "end": False}

        
    def __reply(self, utt):
        results = self.es.search(index='dialogue_pair',
                    body={'query':{'match':{'query':utt}}, 'size':10,})
        return [(result['_source']['query'], result['_source']['response'], result["_score"]) for result in results['hits']['hits']]

    def __reply_nega(self, utt):
        results = self.es.search(index='dialogue_pair_nega',
                    body={'query':{'match':{'query':utt}}, 'size':100,})
        return [(result['_source']['query'], result['_source']['response'], result["_score"]) for result in results['hits']['hits']]    
        
    def evaluate(self, utt, pair):
        return self.evaluator.evaluate(utt, pair[1])