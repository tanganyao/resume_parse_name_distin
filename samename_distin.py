#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time,re,sys, urllib2,urllib,optparse,json,glob,operator,os
reload(sys)
sys.setdefaultencoding('utf-8')

l_person = []    #同名人物列表
l_index = []    #重名人物索引

schoolsuffix = u'中学|分校|大学|学院|党校|学校|中$' #学校后缀
majorsuffix = u'专业|系' #专业后缀

ntsuffix = u'公司|集团|企业|厂|店|所|院|厅|/nc ' #机构后缀
departmentsuffix = u'/nt |中心|部|组|队|科|处' #部门后缀


prewtag = u'历任|曾任|任职|兼任|担任|出任|工作|先后|就任|供职|就职|入职|就职|职于|职於|创办|创立|设立|创建|任教|加盟|组建|加入|进入|/t 入|/t 在|/t 任|/t 于|/t 於' #曾任提示
curwtag = u'现任|今任|至今|目前|起任|现在' #现任提示



positiontag = u'经理.*?|董事.*?|监事.*?|秘书|主任|主席|书记|总监|会计|师|长|员|官' #职位提示
ptagmv = u'等职|职务' #删除职务多余信息
onamestarttag = u'入|在|任|于|於' #职务或者机构提示


department = u'生产科|办公厅|视讯部|大客户部|资产管理部|研究发展部|事业部|供应部|行政部|运输部|财务处|技术部|市场部|质检部|标准化部|研发部|财务部|财务科|销售经理|投融资|信息中心|董事' + \
             u'监事会|董事会|分公司|博士生|党总支|总经理|副总经理|总经理助理' #部门后缀  目前没用

curorgrep = u'公司|本公司|有限公司|股份公司|集团|本集团' #替换成当前公司名  

class person:
	
	def __init__(self, content):
		self.sourceinfo = content
		self.name = ''
		self.birth = ''
		self.sex = ''
		self.nationality = ''
		self.degree = ''
		self.school = []
		self.joblist=[]

	def hasspecialstrings(self, strcontent,strings):
		if re.match(re.compile(u'^(.*?)(' + strings + ')(.*?)$'), strcontent)== None:
			return False
		else:
			return True

	#############################################################################################################
	def getsex(self):
		strbase = re.split(u'；|。|！',self.sourceinfo[3])[0]
		if strbase.find(u'男/b ') > 0 or strbase.find(u'先生/n') > 0:
			self.sex = '男'
			#return u'男'
		elif strbase.find(u'女/b ') > 0 or strbase.find(u'女士/n') > 0:
			self.sex = '女'
			#return u'女'

	def getnationality(self):
		reg = re.compile(u' ([^ ]+/ns .?籍)/',re.S)
		reg1 = re.compile(u' ([^ ]+/[a-zA-Z0-9] 国籍)/',re.S)
		m = reg.search(self.sourceinfo[3])
		m1 = reg1.search(self.sourceinfo[3])
		if m:
			nationality = re.sub('/ns +','',m.group(1))
			self.nationality = nationality
		elif m1:
			nationality = re.sub('/[a-zA-Z0-9]+ ','',m1.group(1))
			self.nationality = nationality

	def getbirth(self):
		strbase = re.split(u'；|。|！',self.sourceinfo[3])[0]
		reg = re.compile(u' ([^ ]+)/t .?生/',re.S)
		reg1 = re.compile(u'生[^，|、|,]+ ([^ ]+)/t ',re.S)
		m = reg.search(strbase)
		m1 = reg1.search(strbase)
		if m:
			self.birth = m.group(1)
			#return m.group(1)
		elif m1:
			self.birth = m1.group(1)
			#return m1.group(1)

	def getdegree(self):
		degree_list = [u'博士',u'硕士',u'工商管理',u'EMBA',u'MBA',u'研究生',u'本科',u'学士', u'专科',u'大专',
					   u'中专', u'高中', u'职高', u'初中', u'学历',u'文凭',u'学位']
		strdegree = ''
		strdegreet = ''
		dindex = -1
		dindext = -1
		for i in re.split(u'/[a-zA-Z0-9]+ ',self.sourceinfo[3]):
			if i in degree_list:
				strdegreet += i
				dindextt = degree_list.index(i)
				if dindext == -1 or dindextt < dindext:
					dindext = dindextt
			else:
				if strdegreet:
					if dindex == -1 or dindext < dindex:
						strdegree = strdegreet
						dindex = dindext
					strdegreet = ''
		self.degree = strdegree

	###############################学校信息######################################################################
	#####################################school info##########################################################
	def getshnameandmajor(self, strshinfo,nextstr):
		strshname = ''
		strmajor = ''
		if self.hasspecialstrings(strshinfo,majorsuffix):
			reg = re.compile('^([^ ]+(' + schoolsuffix +'))(.*?(' + majorsuffix +'))(.*?)$',re.S)
			m = re.match(reg,strshinfo)
			if m:
				strshname = m.group(1)
				strmajor = m.group(3)	
		elif nextstr:
			reg = re.compile('^([^ ]+(' + schoolsuffix +'))(.*?)$',re.S)
			m = re.match(reg,strshinfo)
			if m:
				strshname = m.group(1)
			for nt in re.split(u'，|、|,',nextstr):
				if len(nt) > 5 :
					if self.hasspecialstrings(nt,majorsuffix) and not self.hasspecialstrings(nt,schoolsuffix):
						reg = re.compile('^([^ ]+(' + majorsuffix +'))(.*?)$',re.S)
						m = re.match(reg,nt)
						if m:
							strmajor = m.group(1)
					break
		else:
			reg = re.compile('^([^ ]+(' + schoolsuffix +'))(.*?)$',re.S)
			m = re.match(reg,strshinfo)
			if m:
				strshname = m.group(1)
		return {'shname':strshname,'major':strmajor}

	def getschoolall(self,strshinfo,index):
		lschool = []
		strschool = ''
		reg = re.compile(u'(毕业於|毕业于|就读于|就读|持有|获得|持|获)([^ ]*?(' + schoolsuffix +u').*?)(，|、|,|$)',re.S)
		reg1 = re.compile(u'(系|从|於|于|，|、|,|^)([^ ]*?(' + schoolsuffix +u').*?)毕业',re.S)

		m = reg.search(strshinfo)
		m1 = reg1.search(strshinfo)

		if m:
			strschool = m.group(2)
			strshinfo = strshinfo[strshinfo.find(strschool)+len(strschool):len(strshinfo)]
			lschool.append(self.getshnameandmajor(strschool,strshinfo))
			reg = re.compile(u'(，|、|,|)([^ ]*?(' + schoolsuffix +u').*?)(，|、|,|$)',re.S)
			while(1):
				m = reg.search(strshinfo)
				if m:
					strschool = m.group(2)
					strshinfo = strshinfo[strshinfo.find(strschool)+len(strschool):len(strshinfo)]
					lschool.append(self.getshnameandmajor(strschool,strshinfo))
				else:
					break
		elif m1:
			strschool = m1.group(2)
			for sh in re.split(u'，|、|,',strschool):
				lschool.append(self.getshnameandmajor(sh,''))
		elif index == 0:
			for sh in re.split(u'，|、|,',strshinfo):
				if self.hasspecialstrings(sh,schoolsuffix):
					lschool.append(self.getshnameandmajor(sh,''))
		return lschool

	def getschooltime(self,strshinfo):
		reg = re.compile(u'^([^ ]+)/t ((，|、|,)/[a-zA-Z]+ )?[^，|、|,]+(' + schoolsuffix + ')',re.S)
		m = reg.search(strshinfo)
		if m:
			return m.group(1)
		else:
			return ''

	def getschool(self):
		schoollist = []
		lsentence = re.split(u'；|。|！',self.sourceinfo[3]) #分句
		for i in range(len(lsentence)):
			strnotag = re.sub('/[a-zA-Z0-9]+ ','',lsentence[i])
			reg = re.compile(u'([^ ]{2,}(' + schoolsuffix +'))',re.S)
			m = reg.search(strnotag)
			if m:
				tsentencenotag = ''
				tsentence=''
				for sentence in re.split('([^ ]+/t )',lsentence[i]):
					tsentence += sentence
					sentencenotagd = re.sub('/[a-zA-Z0-9]+ ','',sentence)
					tsentencenotag += sentencenotagd
					if sentence.find('/t ') < 0 and len(sentencenotagd) > 2:
						if self.hasspecialstrings(tsentencenotag,schoolsuffix):
							strtime = self.getschooltime(tsentence)
							schoollist += [{'time':strtime,'shname':shi['shname'],'major':shi['major']} for shi in self.getschoolall(tsentencenotag,i)]
						tsentence = ''
						tsentencenotag = ''
		#return schoollist
		self.school = schoollist

	########################################work info###########################################################
	####################################################work info###########################################################################
	def getworktime(self,strwork):
		reg = re.compile(u'^(.*/t )',re.S)
		m = reg.search(strwork)
		if m:
			return m.group(1)
		else:
			return ''

	def getcurworktime(self,strwork):
		reg = re.compile(u'^(.*?(' + curwtag + u'))',re.S)
		m = reg.search(strwork)
		if m:
			return re.sub(u'^.*(，|、|,)','',m.group(1))
		else:
			return ''

	def getrightorg(self,strorg,strpos,strtime,type):
		#print strorg,'ooooooo',strpos,'oooooo',type
		m = re.match(re.compile('^.*(' + curwtag + '|' + prewtag + '|' + onamestarttag + ')(.{2,})$'), strorg)
		if m:
			strorg = m.group(2)
		# strorg = re.sub('^(' + curorgrep + ')',sourceinfo[0],strorg)

		strpos = re.sub('(' + ptagmv + '){0,2}$','',strpos)
		m = re.match(re.compile('^.*(' + curwtag + '|' + prewtag + '|' + onamestarttag + ')(.{2,})$'), strpos)
		if m:
			strpos = m.group(2)

		# print strorg,'ooooooo',strpos

		if self.hasspecialstrings(strorg,ntsuffix) and strpos:
			reg = re.compile(u'^(.*(' + ntsuffix + '))(.*?)$')
			m = re.match(reg,strorg)
			if m:
				strorg = m.group(1)
				strpos = m.group(3) + strpos
		elif strorg.find('/ns ') >= 0:
			reg = re.compile(u'^(.*(' + departmentsuffix + '))(.*?)$')
			m = re.match(reg,strorg)
			if m:
				strorg = m.group(1)
				strpos = m.group(3) + strpos
		elif len(strorg) >= 8:
			pass
		else:
			strpos = strorg + strpos
			strorg = ''
		oplist = []
		strorg = re.sub('/[a-zA-Z0-9]+ ','',strorg)
		strpos = re.sub('/[a-zA-Z0-9]+ ','',strpos)
		if strorg:
			reg = re.compile(u'^(.{2,})(和|与)(.{2,})$')
			m = re.match(reg,strorg)
			if m:
				oplist.append({'time':strtime,'org':m.group(1),'pos':''})
				oplist.append({'time':strtime,'org':m.group(3),'pos':strpos})
			else:
				oplist.append({'time':strtime,'org':strorg,'pos':strpos})
		else:
			oplist.append({'time':strtime,'org':strorg,'pos':strpos})
		return oplist

	def parseop(self,strwork,strtime):
		# print strwork,'------------------'
		oplist = []
		reg = re.compile('^.*(' + curwtag + '|' + prewtag + '|' + onamestarttag +')([^' + curwtag + '|' + prewtag + '|' + onamestarttag +']{2,})(' + \
						 curwtag + '|' + prewtag + '|' + onamestarttag +')(.{2,})$',re.S)#在org任pos
		m = re.match(reg,strwork)
		if m:
			oplist += self.getrightorg(m.group(2),m.group(4),strtime,1)
			return oplist
		reg = re.compile('^.*(' + curwtag + '|' + prewtag + '|' + onamestarttag +')(.{0,}(' + ntsuffix + '|' + departmentsuffix +'))(.{2,})$',re.S)#任org+pos
		m = re.match(reg,strwork)
		if m:
			oplist += self.getrightorg(m.group(2),m.group(4),strtime,2)
			return oplist
		reg = re.compile('^(.{0,}(' + ntsuffix + '|' + departmentsuffix +'))(' + curwtag + '|' + prewtag + '|' + onamestarttag +')(.{2,})$',re.S)#org任pos
		m = re.match(reg,strwork)
		if m:
			oplist += self.getrightorg(m.group(1),m.group(4),strtime,3)
			return oplist
		reg = re.compile('^(.{0,}(' + ntsuffix + '|' + departmentsuffix +'))(.{2,})$',re.S)#orgpos
		m = re.match(reg,strwork)
		if m:
			oplist += self.getrightorg(m.group(1),m.group(3),strtime,4)
			return oplist
		oplist += self.getrightorg('',strwork,strtime,5)
		return oplist

	def getorgandpos(self,strworkinfo):
		#print strworkinfo,'000000000000000000'
		ostart = False
		oplist = []
		curoplist = []
		strtime = self.getworktime(strworkinfo)
		strcurtime = self.getcurworktime(strworkinfo)
		#print strtime,'--------',strcurtime
		for work in re.split(u'，|、|,',strworkinfo):
			# if hasspecialstrings(work,curwtag + '|' + prewtag + '|' + onamestarttag) and not ostart:
			#     ostart = True
			# if ostart:
			#print work, '!!!!!!!!!!!!!!!!!!!!!!!!!!!'
			strcurtimetmp = self.getcurworktime(work)
			work = re.sub('^.*/t ','',work)
			if re.match(re.compile(u'^(.*?)(' + positiontag +u')$'), work):
				if strcurtimetmp:
					curoplist += self.parseop(work,strcurtimetmp)
				else:
					if strcurtime:
						curoplist += self.parseop(work,strcurtime)
					else:
						oplist += self.parseop(work,strtime)

			else:
				if strcurtimetmp:
					curoplist += self.getrightorg(work,'',strcurtimetmp,0)
				else:
					if strcurtime:
						curoplist += self.getrightorg(work,'',strcurtime,0)
					else:
						oplist += self.getrightorg(work,'',strtime,0)


		olist = [op for op in oplist if op['org']]
		plist = [op for op in oplist if op['pos']]
		if len(olist) == 1 and len(plist) > 1:
			oplist = [{'time':p['time'],'org':olist[0]['org'],'pos':p['pos']} for p in plist]
		elif len(plist) == 1 and len(olist) > 1:
			oplist = [{'time':o['time'],'org':o['org'],'pos':plist[0]['pos']} for o in olist]
		elif len(plist) == 1 and len(olist) == 1:
			oplist = [{'time':olist[0]['time'],'org':olist[0]['org'],'pos':plist[0]['pos']}]

		olist = [op for op in curoplist if op['org']]
		plist = [op for op in curoplist if op['pos']]
		if len(olist) == 1 and len(plist) > 1:
			curoplist = [{'time':p['time'],'org':olist[0]['org'],'pos':p['pos']} for p in plist]
		elif len(plist) == 1 and len(olist) > 1:
			curoplist = [{'time':o['time'],'org':o['org'],'pos':plist[0]['pos']} for o in olist]
		elif len(plist) == 1 and len(olist) == 1:
			curoplist = [{'time':olist[0]['time'],'org':olist[0]['org'],'pos':plist[0]['pos']}]

		return oplist,curoplist

	def getworkexperience(self,tsentence,tsentencenotag):
		# print tsentencenotag,'pppppppppppp'
		oplist = []
		curoplist = []
		if self.hasspecialstrings(tsentencenotag,curwtag + '|' + prewtag) or re.match(re.compile(u'^(.*?)(' + positiontag +u')(，|、|,|$)'), tsentencenotag): #含职位或者职位提示
			strwork = ''
			reg = re.compile('(' + curwtag + '|' + prewtag + '|' + onamestarttag +')(.{0,}(' + positiontag +u'))(，|、|,|$)',re.S) #含职位和职位提示
			while(1):
				m = reg.search(tsentencenotag)
				if m:
					strwork = m.group(2)
					strworkhead = tsentencenotag[0:tsentencenotag.find(strwork)]	#head this tag
					tsentencenotag = tsentencenotag[tsentencenotag.find(strwork)+len(strwork):len(tsentencenotag)] #tail this tag
					if not self.hasspecialstrings(strworkhead,u'毕业於|毕业于|就读于|就读|持有|获得|/t 生|生[^，|、|,]+ ([^ ]+)/t '):
						strwork = strworkhead + strwork
					o,c = self.getorgandpos(strworkhead + strwork)
					oplist += o
					curoplist += c
				else:
					reg = re.compile('(' + curwtag + '|' + prewtag + '|' + onamestarttag +')(.{0,}(' + ntsuffix + '|' + departmentsuffix +u').*?)(，|、|,|$)',re.S)  #含部门和职位提示
					reg1 = re.compile('^.*(；|。|！|，|、|,|：|:)(.{0,}(' + ntsuffix + '|' + departmentsuffix +u').{0,}(' + positiontag +u'))(，|、|,|$)',re.S) #含部门和职位
					m = reg.search(tsentencenotag)
					m1 = reg1.search(tsentencenotag)
					if m:
						# print '2222222222'
						strwork = m.group(2)
						strworkhead = tsentencenotag[0:tsentencenotag.find(strwork)]
						o,c = self.getorgandpos(strworkhead + strwork)
						oplist += o
						curoplist += c
					elif m1:
						# print '33333333'
						strwork = m1.group(2)
						o,c = self.getorgandpos(strwork)
						oplist += o
						curoplist += c
					break

		return oplist,curoplist

	def getwork(self):
		lsentence = re.split(u'；|。|！',self.sourceinfo[3]) #分句
		#print '################################################'
		oplist = []
		curoplist = []
		for i in range(len(lsentence)):
			tsentencenotag = ''
			tsentence=''
			for sentence in re.split('([^ ]+/t )',lsentence[i]): #时间分割
				tsentence += sentence
				sentencenotagd = re.sub('/(?!(nt |nc |ns |t ))[a-zA-Z0-9]+ ','',sentence)
				tsentencenotag += sentencenotagd
				if sentence.find('/t ') < 0 and len(sentencenotagd.replace(' ','')) > 2:
					o,c = self.getworkexperience(tsentence,tsentencenotag)
					oplist += o
					curoplist += c
					tsentence = ''
					tsentencenotag = ''
		
		for cwork in oplist:
			if len(cwork['org'])>2:
				self.joblist.append(cwork['org'])
		for pwork in curoplist:
			if len(pwork['org'])>2:
				self.joblist.append(pwork['org'])

	####################################################################################################################################
	#def getbaseinfo():

	###################################################distinguish samename######################################
	'''
					person_data['person_basic_bnfo']['sex'] == p[1]['person_basic_bnfo']['sex'] and \
					person_data['person_basic_bnfo']['nationality'] == p[1]['person_basic_bnfo']['nationality']:
	'''

################################################################################################################
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

#########################################将index插入到对应组中##################################################
def insert_index(per, index):
	flag = 0 #判断是否跳出循环
	for i, m in enumerate(l_index):
		#if len(m) > 1:	
		for n in m:
			if n == per[0]:
				#print n,i
				l_index[i].append(index)
				flag = 1
				break
		if flag == 1:
			break
	return True

#####################################################判断学校,工作是否有重叠##########################################
def job_overlap(p, per):

	for job in p.joblist:
		for per_job in per[1].joblist:
			if job == per_job:
				return True
	return False

def Sch_overlap(p, per):
	l_psh = [l['shname'] for l in p.school]
	l_persh = [l['shname'] for l in per[1].school]
	for psh in l_psh:
		#print psh+'*********************'
		if psh != '':
			if psh in l_persh:
				return True
			else:
				for persh in l_persh:
					if psh in persh or persh in psh:
						return True
	return False

def samename_distinguish(index, p):
	#info = [index, person_data]
	p.name = p.sourceinfo[1]
	p.getsex()
	p.getnationality()
	p.getbirth()
	p.getdegree()
	p.getschool()
	p.getwork()

	#print '\n'.join(p.joblist).encode('gb2312')
	flag = 0
	if len(l_index) == 0:
		l_index.append([index])
		l_person.append((index, p))
	else:
		for per in l_person:
			#print per[1].birth+'***************'
			#判定函数
			if p.birth == '':
				#调用学校判定函数, 返回true,则含有, false则没有
				if p.name == per[1].name and Sch_overlap(p, per) and p.degree == per[1].degree and job_overlap(p, per):
					#调用插入函数, 将index插入到对应组中
					###
					if insert_index(per, index):
						break
				else:
					flag += 1
			elif p.birth == per[1].birth:
				#判定学位和性别
				if p.name == per[1].name and per[1].degree == p.degree and job_overlap(p, per):
					#调用插入函数, 将index插入到对应组中
					if insert_index(per, index):
						break
				else:
					flag += 1
			elif p.name == per[1].name and per[1].birth != '' and (p.birth.strip() in per[1].birth.strip() or per[1].birth.strip() in p.birth.strip()):
				#调用学校判定函数
				#print p.birth+'#############'+per[1].birth
				if per[1].degree == p.degree:
					if Sch_overlap(p, per) and job_overlap(p, per):
						#调用插入函数, 将index插入到对应组中
						if insert_index(per, index):
							break
					else:
						flag += 1
						#print '***************************'
				else:
					flag += 1
			else:
				#生日不等
				flag += 1
		if flag == len(l_person):
			l_index.append([index])
		#print l_person
		l_person.append((index, p))

#############################################################################################################
#对行进行分析，传入行数据和index(对应的行数)
def doParse(linestr, index):

	l_content =  linestr.split('<===>')
	p = person(l_content)
	#print p
	if len(l_content) < 3:
		print('data type problem')
		return
	else:
		p.sourceinfo.append(getSegString(l_content[2]))
		#print sourceinfo[3]
		#getbaseinfo()
		#getworkinfo()
		#printpersondata()
		samename_distinguish(index,p)

###############################################################################################################
#添加index
def readfile(file):
	for index, line in enumerate(file.readlines()[:200]):
		line = line.decode('utf-8')
		doParse(line, index)
	print l_index
	#print l_person[1][1].person_data

##############################################################################################################
def command_line():
    opt = optparse.OptionParser(usage="usage: %prog [OPTION]... [FILE]...")
    opt.add_option("-f", "--file", dest="filename", metavar="INFILE",
                   help="input FILE")
    opt.add_option("-o", "--outfile", dest="outfilename", metavar="OUTFILE",
                   help="write output to FILE ")
    opt.add_option("-m", "--formart", dest="outformart", metavar="OUTFORMART",
                   help=" output formart ")

    (options, args) = opt.parse_args()
    global  outformart
    outformart = options.outformart
##    if not args:
##        opt.print_help()

    if not options.filename: readfile(sys.stdin)
    else:
        f = open(options.filename)
        readfile(f)
        f.close()


if __name__ == "__main__":
    command_line()