class Test:
	def p(self):
		print("aaaaaaaaaaaaaaaaa")
 
a = Test()
b = locals()
for xx in range(97, 123):
	#t = 'p'+str(xx) + '=Test()'
	#print t
	#exec(t)
	b['b'+str(xx)]  = Test()
    #print eval(chr(xx))
	t = b['b'+str(xx)]
	print t.p()
print a
#print z