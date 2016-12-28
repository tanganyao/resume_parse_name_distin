 python resumeparse.py  -f company_nr_0311.txt


服务器上的分词工具调用：
def getSegString(strcontent):
    strcontent = strcontent.replace('\\','').replace('\t','').replace('\n','').replace('"','\\"')
    strarticle = '{"content": "'+strcontent+'"}'
    article = json.loads(strarticle)
    postjson = json.loads('{"pos": "1", "utf": "1", "entity": "1", "merge": "1", "rtiment": "1", "rentity": "1"}')
    postjson['article'] = article
    req = urllib2.urlopen('http://21.raisound.com:12550', json.dumps(postjson))
    segcontent = req.read().decode('gbk')
    strc = json.loads(segcontent)['content']
    return strc
