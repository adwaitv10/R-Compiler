#!/usr/bin/python
import sys

#math_op = ['+','-','/','%','*']
math_op = {'+':'add', '-':'sub', '*':'mult', '/':'div', '%':'div'}
#rel_op = ['==','!=','<','>','<=','>=']
rel_op = {'==':'beq','!=':'bne','<':'blt','>':'bgt','<=':'ble','>=':'bge'}
as_op = ['=']

operators = math_op.keys() + rel_op.keys() + as_op

keywords = ['Array','print','scan','ifgoto','goto','newline','exit', '[', ']']
ids = {}

def get_identifiers(line):
	flag = 0
	if(line[1] == "Array"):
		flag = int(line[3])
	for word in line:
		if word in ids.keys():
			continue 
		if word not in keywords and word.isdigit() == False and word not in operators:
			if(flag == 0):
				ids[word] = 0
			else:
				ids[word] = flag
 

def read3ac(file):
	tac = []
	for line in file:
		temp = line.strip().split(' ')
		tac.append(temp)
		get_identifiers(temp) #values updated in ids
	return tac

def declare_ids():  #initializing the identifiers to zero in mips
	temp = []
	for identifier in ids.keys():
		if(ids[identifier] == 0):
			temp.append(str(identifier) + ": .word 0")
		else:
			temp.append(str(identifier) + ": .space " + str(ids[identifier]))
	return temp

def leaders(tac):
	temp = [0]*len(tac)
	for index,line in enumerate(tac):
		
		if(index==0):
			temp[index]=1
		
		if(line[1] == "goto" or line[1] == "if"):
			target = int(line[-1])
			temp[index+1] = 1
			temp[target-1] = 1

	return temp

#returns a dictionary with keys for block numbers and values carrying their code
def get_blocks(tac):
	isleader = leaders(tac)
	blocks = {}
	temp = 0
	for index,line in enumerate(tac):
		if isleader[index] == 1:
			temp+=1
			blocks[temp] = []
			blocks[temp].append(line)
		else:
			blocks[temp].append(line)
	return blocks



def code_math(line):
	temp = []
	#temp.append("lw\t $t1, " + str(line[1]))

	if(math_op[line[2]] == 'add' or math_op[line[2]] == 'sub'):
		if(line[3].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[3]))
		else:
			temp.append("li\t $t2, " + str(line[3]))
		
		if(len(line) == 5):
			if(line[4].isdigit() == False):
				temp.append("lw\t $t3, " + str(line[4]))
			else:
				temp.append("li\t $t3, " + str(line[4]))

		temp.append(str(math_op[line[2]]) + "\t $t1, $t2, $t3")
		temp.append("sw\t $t1, " + str(line[1]))

	else:
		if(line[3].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[3]))
		else:
			temp.append("li\t $t2, " + str(line[3]))

		if(line[4].isdigit() == False):
			temp.append("lw\t $t3, " + str(line[4]))
		else:
			temp.append("li\t $t3, " + str(line[4]))

		temp.append(str(math_op[line[2]]) + "\t $t2, $t3")
		temp.append("mfhi\t $t0")
		temp.append("mflo\t $t1")
		if(line[2] == '%'):
			temp.append("sw\t $t0, " + str(line[1]))
		else:
			temp.append("sw\t $t1, " + str(line[1]))
	return temp


def code_print(line):
	temp = []
	temp.append("li\t $v0, 1")
	if(line[2] == "newline"):
		temp.append("li\t $v0, 4")
		temp.append("la\t $a0, newline")
	else:
		temp.append("lw\t $t1, " + str(line[2]))
		temp.append("move $a0, $t1")
	temp.append("syscall")
	return temp


def code_scan(line):
	temp = []
	temp.append("li\t $v0, 5")
	temp.append("syscall")
	temp.append("sw $v0, " + str(line[2]))
	return temp


def code_asgn(line):
	temp = []
	if(len(line) == 4):
		if(line[3].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[3]))
		else:
			temp.append("li\t $t2, " + str(line[3]))
		temp.append("sw\t $t2, " + str(line[1]))

	elif(line[4] == '['):
		temp.append("la\t $t3, " + str(line[3]))
		if(line[5].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[5]))
		else:
			temp.append("li\t $t2, " + str(line[5]))
		temp.append("add\t $t2, $t2, $t2")
		temp.append("add\t $t2, $t2, $t2")
		temp.append("add\t $t1, $t2, $t3")
		temp.append("lw\t $t4, 0($t1)")
		temp.append("sw\t $t4, " + str(line[1]))

	elif(line[2] == '['):
		if(line[6].isdigit() == False):
			temp.append("lw\t $t4, " + str(line[6]))
		else:
			temp.append("li\t $t4, " + str(line[6]))
		temp.append("la\t $t3, " + str(line[1]))
		if(line[3].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[3]))
		else:
			temp.append("li\t $t2, " + str(line[3]))
		temp.append("add\t $t2, $t2, $t2")
		temp.append("add\t $t2, $t2, $t2")
		temp.append("add\t $t1, $t2, $t3")
		temp.append("sw\t $t4, 0($t1)")
		
	return temp


def jump_target(line,blocks):
	label = int(line[-1])
	length = 1
	target = 0
	for i in blocks.keys():
		if(label == length):
			target = i
			break
		length += len(blocks[i])
	return target


def code_jumps(line, target):
	temp = []
	if(line[1] == "goto"):
		temp.append("j Block" + str(target))
	else:
		if(line[2].isdigit() == False):
			temp.append("lw\t $t1, " + str(line[2]))
		else:
			temp.append("li\t $t1, " + str(line[2]))

		if(line[4].isdigit() == False):
			temp.append("lw\t $t2, " + str(line[4]))
		else:
			temp.append("li\t $t2, " + str(line[4]))

		temp.append(str(rel_op[line[3]]) + "\t $t1, $t2, Block" + str(target))
	
	return temp






filename = sys.argv[1]
file = open(filename, 'r')

#code3ac is a list of lists, each list has seperate elements for op ids, Array etc. ex. [['Array','b','20'],['Array','a','10']]
code3ac = read3ac(file)

#Stores all the blocks in a dictionary
blocks = get_blocks(code3ac)

file.close()

mips_code = []

mips_code.append(".data")
mips_code+=declare_ids()
mips_code.append('newline: .asciiz "\n"')

mips_code.append("\n.text")
mips_code.append("main:")



for i in blocks.keys():
	#last_line = len(blocks[i]) - 1
	mips_code.append("Block" + str(i) + ": ")
	for index,line in enumerate(blocks[i]):
		if(line[2] in math_op.keys()):
			mips_code+= code_math(line)
		elif(line[2] in as_op):
			mips_code += code_asgn(line)
		elif(len(line) == 7 and line[5] in as_op):
			mips_code += code_asgn(line)
		elif(line[1] == "print"):
			mips_code+= code_print(line)
		elif(line[1] == "scan"): 
			mips_code+= code_scan(line)
		elif(line[1] == "goto" or line[1] == "if"):
			target = jump_target(line, blocks)
			mips_code += code_jumps(line, target)
		elif(line[1] == "exit"):
			mips_code.append("li\t $v0, 10")
			mips_code.append("syscall")
			


filenew = open("result.asm", 'w')

for line in mips_code:
	filenew.writelines(line+"\n")
filenew.close()