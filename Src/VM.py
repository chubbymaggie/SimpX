import sys
import TaintAnalysis as TaintAnalysis
import SymbolicExecution as SymbolicExecution

performTaint = False
performSE = False
taint = None

# Function to run the virtual machine
def run(instructions, symbolTable, l_performTaint, l_performSE, ):

	# Will enable or disable taint analysis and symbolic execution
	global performTaint, performSE
	performTaint = l_performTaint
	performSE = l_performSE
	if (performTaint):
		global taint
		taint = TaintAnalysis.TaintAnalysis()

	# Initialize memory and the program counter
	memory = [None] * 65536
	programCounter = 0

	print("\n::======= EXECUTE LOOP STARTED =======::\n")
	while True:
		# Execute the next instruction and return the updated program state
		programState = __execute(instructions, programCounter, symbolTable, memory)
		
		# Next instruction to execute, update symbol table, updated memory contents
		programCounter = programState[0]
		symbolTable = programState[1]
		memory = programState[2]

		# Check our program's status
		if programCounter == -1:
			print("Program encounter an error! Aborted!")
			break
		if programCounter == -2:
			print("Program terminated successfully.")
			break
		if programCounter == -3:
			print("Segmentation Fault!")
			break
		if programCounter == -4:
			print("Assertion fail! Quitting.")
			break

	print("\n::======= EXECUTE LOOP END =======::\n")
	print("::======= MACHINE END STATE =======::")
	print("\n::VARIABLES::\n")
	for key, value in symbolTable.items():
		if key[0] != 't':
			print("%s = %s") % (key[4:], value)
	print("\n::MEMORY::\n")
	for x in range(len(memory)):
		if memory[x] != None:
			print("Memory[ %d ] = %d") % (x, memory[x])
	print("\n")
	if (performTaint):
		print("\n::== TAINT STATUS ==::")
		global taint
		taint.printTaintedResults()

	return symbolTable
		

# Function to execute each instruction
def __execute(instructions, programCounter, symbolTable, memory):
	instruction = instructions[programCounter]
	# Perform unary operation
	if instruction.instruction_type == "UN_OP":
		programState = __unOpInst(instruction, programCounter, symbolTable, memory)
	# Perform binary operation
	elif instruction.instruction_type == "BIN_OP":
		programState = __binOpInst(instruction, programCounter, symbolTable, memory)
	# Perform input
	elif instruction.instruction_type == "INPUT":
		programState = __inputInst(instruction, programCounter, symbolTable, memory)
	# Print output
	elif instruction.instruction_type == "PRINT_OUTPUT":
		programState = __printOutInst(instruction, programCounter, symbolTable, memory)
	# Assign values
	elif instruction.instruction_type == "ASSIGN":
		programState = __assignInst(instruction, programCounter, symbolTable, memory)
	# Goto (must take all the instructions to calculate where to return to)
	elif instruction.instruction_type == "GOTO":
		programState = __gotoInst(instructions, programCounter, symbolTable, memory)
	# Store 
	elif instruction.instruction_type == "STORE":
		programState = __storeInst(instruction, programCounter, symbolTable, memory)
	# Load
	elif instruction.instruction_type == "LOAD":
		programState = __loadInst(instruction, programCounter, symbolTable, memory)
	# Assert
	elif instruction.instruction_type == "ASSERT":
		programState = __assertInst(instruction, programCounter, symbolTable, memory)
	# Boolean (must take all the instructions to calculate where to return to)
	elif instruction.instruction_type == "BOOLEAN":
		programState = __booleanInst(instructions, programCounter, symbolTable, memory)
	# Check for terminate statement
	elif instruction.instruction_type == "TERMINATE_PROGRAM":
		programState = (-2, symbolTable, memory)
	# Keep the program going even if we don't recognize the instruction (consider error instead)
	else:
		programState = (programCounter + 1, symbolTable, memory)
		
	# Return the updated program state
	return programState

# Function to perform the unary operation instructions
def __unOpInst(instruction, programCounter, symbolTable, memory):
	print("Executing unary op instruction.")
	lhs = __symTableLookUp(instruction.data[1], symbolTable)
	rhs = __symTableLookUp(instruction.data[3], symbolTable)

	# Check for correct operation symbol
	if instruction.data[2] == '*':
		answer = lhs * rhs
	if instruction.data[2] == '+':
		answer = lhs + rhs
	if instruction.data[2] == '-':
		answer = lhs - rhs

	# Update the answer
	symbolTable[instruction.data[0]] = answer

	# Perform taint analysis if option is set
	if (performTaint):
		global taint
		taint.propagateTaintBinOp(instruction.data[0], instruction.data[1], instruction.data[3], instruction.data[2])

	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function to perform the binary operation instructions
def __binOpInst(instruction, programCounter, symbolTable, memory):
	print("Executing binary op instruction.")
	lhs = __symTableLookUp(instruction.data[1], symbolTable)
	rhs = __symTableLookUp(instruction.data[3], symbolTable)
	
	# Check for correct operation symbol
	if instruction.data[2] == '*':
		answer = lhs * rhs
	if instruction.data[2] == '/':
		answer = math.floor(lhs / rhs)
	if instruction.data[2] == '+':
		answer = lhs + rhs
	if instruction.data[2] == '-':
		answer = lhs - rhs
	if instruction.data[2] == '^':
		answer = lhs ^ rhs
	if instruction.data[2] == '|':
		answer = lhs | rhs
	if instruction.data[2] == '&':
		answer = lhs & rhs
	if instruction.data[2] == '%':
		answer = lhs % rhs

	# Update the answer
	symbolTable[instruction.data[0]] = answer

	# Perform taint analysis if option is set
	if (performTaint):
		global taint
		taint.propagateTaintBinOp(instruction.data[0], instruction.data[1], instruction.data[3], instruction.data[2])

	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function to perform the input operation instructions
def __inputInst(instruction, programCounter, symbolTable, memory):
	print("Executing input instruction.")
	print("User input interrupt! Enter an integer:")
	while True:
		sys.stdout.write(">>> ")
		try:
			user_input = int(raw_input())
			break
		except ValueError:
			print("\nONLY INTEGERS ACCEPTED!")
			print("Enter an integer:")
	
	symbolTable[instruction.data[0]] = user_input
	
	# Perform taint analysis if option is set
	if (performTaint):
		global taint
		taint.propagateTaintInput(instruction.data[0])

	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function to perform output instructions
def __printOutInst(instruction, programCounter, symbolTable, memory):
	print("Executing print instruction.")
	print("Console output interrupt.")
	value = __symTableLookUp(instruction.data[0], symbolTable)
	print(">>> %d") % (value)
	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function perform assignment instructions
def __assignInst(instruction, programCounter, symbolTable, memory):
	print("Executing assign instruction.")
	symbolTable[instruction.data[0]] = __symTableLookUp(instruction.data[1], symbolTable)
	
	# Perform taint analysis if option is set
	if (performTaint):
		global taint
		taint.propagateTaintAssign(instruction.data[0], instruction.data[1])

	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function to perform goto instructions
def __gotoInst(instructions, programCounter, symbolTable, memory):
	print("Executing goto instruction.")
	instruction = instructions[programCounter]
	target_address = "BB_" + str(__symTableLookUp(instruction.data[0], symbolTable)) + ":BEGIN"
	# If we don't find the destination, then we need to crash
	programCounter = -3
	for x in range(len(instructions)):
		if instructions[x].instruction_type == target_address: 
			print("Jumping to: %s") % (target_address)
			programCounter = x
	
	# Check for tainted jump
	if (performTaint):
		taint.taintedJump(instruction.data[0])

	return (programCounter, symbolTable, memory)

# Function to perform store instructions
def __storeInst(instruction, programCounter, symbolTable, memory):
	print("Executing store instruction.")
	destination = __symTableLookUp(instruction.data[0], symbolTable)
	value = __symTableLookUp(instruction.data[1], symbolTable)
	memory[destination] = value
	
	# Propagate taint if option is set
	if (performTaint):
		global taint
		taint.propagateTaintStore(destination, instruction.data[1])

	programCounter += 1
	return (programCounter, symbolTable, memory)

# Function to perform load instructions
def __loadInst(instruction, programCounter, symbolTable, memory):
	print("Executing load instruction.")
	mem_index = __symTableLookUp(instruction.data[1], symbolTable)
	if (memory[mem_index] == None or mem_index < 0):
		programCounter = -3
	else:
		symbolTable[instruction.data[0]] = memory[mem_index]
		programCounter += 1

	# Propagate taint if option is set
	if (performTaint):
		global taint
		taint.propagateTaintLoad(mem_index, instruction.data[0])

	return (programCounter, symbolTable, memory)

# Function to perform assert instructions
def __assertInst(instruction, programCounter, symbolTable, memory):
	print("Executing assert instruction.")
	lhs = __symTableLookUp(instruction.data[0], symbolTable)
	rhs = __symTableLookUp(instruction.data[2], symbolTable)
	if instruction.data[1] == '==':
		if lhs == rhs:
			programCounter += 1
		else:
			programCounter = -4
	if instruction.data[1] == '!=':
		if lhs != rhs:
			programCounter += 1
		else:
			programCounter = -4
	if instruction.data[1] == '<':
		if lhs < rhs:
			programCounter += 1
		else:
			programCounter = -4
	if instruction.data[1] == '>':
		if lhs > rhs:
			programCounter += 1
		else:
			programCounter = -4
	if instruction.data[1] == '<=':
		if lhs <= rhs:
			programCounter += 1
		else:
			programCounter = -4
	if instruction.data[1] == '>=':
		if lhs >= rhs:
			programCounter += 1
		else:
			programCounter = -4
	
	return (programCounter, symbolTable, memory)

# Function to perform boolean instructions
def __booleanInst(instructions, programCounter, symbolTable, memory):
	print("Executing boolean instruction.")
	instruction = instructions[programCounter]
	lhs = __symTableLookUp(instruction.data[0], symbolTable)
	rhs = __symTableLookUp(instruction.data[2], symbolTable)
	
	take_true = False
	if instruction.data[1] == '==':
		if lhs == rhs:
			take_true = True
	if instruction.data[1] == '!=':
		if lhs != rhs:
			take_true = True
	if instruction.data[1] == '<':
		if lhs < rhs:
			take_true = True
	if instruction.data[1] == '>':
		if lhs > rhs:
			take_true == True
	if instruction.data[1] == '<=':
		if lhs <= rhs:
			take_true == True
	if instruction.data[1] == '>=':
		if lhs >= rhs:
			take_true == True

	if take_true == True:
		target_address = "BB_" + str(__symTableLookUp(instruction.data[3], symbolTable)) + ":BEGIN"
	else:
		target_address = "BB_" + str(__symTableLookUp(instruction.data[4], symbolTable)) + ":BEGIN"

	# If we don't find the destination, then we need to crash
	programCounter = -3
	for x in range(len(instructions)):
		if instructions[x].instruction_type == target_address: 
			print("Jumping to: %s") % (target_address)
			programCounter = x

	return (programCounter, symbolTable, memory)

# Function to perform symbol table look ups
def __symTableLookUp(label, symbolTable):
	try:
		int(label)
		return int(label)
	except:
		if label in symbolTable:
			if symbolTable[label] == '':
				return 0
			else:
				return int(symbolTable[label])
		else:
			return 0
