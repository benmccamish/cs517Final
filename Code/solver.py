from pysmt.shortcuts import Symbol, And, GE, LT, Plus, Equals, Int, get_model, Real, LE, Times, Or, Solver, ForAll, NotEquals, Implies, GT, Exists, Not
from pysmt.typing import INT, REAL
import json
import copy


#Set this to True if you want to see a mess
DEBUG=False

def constructRewardMatrix(intents, tuples, matches):
	rewardMatrix = dict()
	for intent in intents:
		rewardMatrix[intent] = dict()
		for tup in tuples:
			if (intent, tup) in matches:
				rewardMatrix[intent][tup] = Real(1)
			else:
				rewardMatrix[intent][tup] = Real(0)

	return rewardMatrix

def minReward(intents, queries, tuples, matches, minRewardValue):
	userStrategy = dict()
	dbmsStrategy = dict()
	rewardMatrix = constructRewardMatrix(intents, tuples, matches)
	letters = set()

	#User Strategy matrix, each cell holds a variable for the SMT
	for intent in intents:
		if intent not in userStrategy:
			userStrategy[intent] = dict()
		for query in queries:
			userStrategy[intent][query] = Symbol('User['+intent + '][' + query + ']', REAL)
			letters.add(userStrategy[intent][query])
			
	#DBMS Strategy matrix, each cell holds a variable for the SMT
	for query in queries:
		if query not in dbmsStrategy:
			dbmsStrategy[query] = dict()
		for tup in tuples:
			dbmsStrategy[query][tup] = Symbol('DBMS['+query + '][' + tup + ']', REAL)
			letters.add(dbmsStrategy[query][tup])

	#Tells the range of values, for now set to Pure strategy so [0,1]
	domains = And([Or(Equals(l, Real(0)), Equals(l, Real(1))) for l in letters])

	#Adds each row of the user strategy
	stochasticMatrixUser = list()
	for intent in intents:
		stochasticMatrixUser.append(Plus(userStrategy[intent].values()))
	
	#Adds each row of the DBMS strategy
	stochasticMatrixdbms = list()
	for query in queries:
		stochasticMatrixdbms.append(Plus(dbmsStrategy[query].values()))
	
	#Checks the rows to make sure that the strategies are row stochastic
	stochUserEquals = [Equals(x, Real(1)) for x in stochasticMatrixUser]
	stochdbmsEquals = [Equals(x, Real(1)) for x in stochasticMatrixdbms]
	allEquals = stochdbmsEquals + stochUserEquals

	#Stochastic problem
	stochasticProblem = And(allEquals)
	if DEBUG:
		print('\nStochastic Serialization: ')
		print(stochasticProblem)
	
	#Uses Formula 1 from my paper to calculate the payoff
	reward = list()
	for intent in intents:
		for query in queries:
			for tup in tuples:
				reward.append(Times(Real(1/len(intents)), userStrategy[intent][query], dbmsStrategy[query][tup], rewardMatrix[intent][tup]))

	#Reward problem, requires a minimum reward. May not always be possible to achieve this reward
	rewardProblem = GE(Plus(reward), Real(minRewardValue))
	if DEBUG:
		print('\nReward Serialization: ')
		print(rewardProblem)

	with Solver(name="z3") as solver:
		solver.add_assertion(domains)
		if not solver.solve():
			print('No solultion available')
			return
		print('Can satisfy domains')

		solver.add_assertion(stochasticProblem)
		if not solver.solve():
			print('No sulution available')
			return
		print('Can satisfy stochastic')
		
		solver.add_assertion(rewardProblem)
		if not solver.solve():
			print('No solution available')
			return
		print('Can satisfy minimum reward')

		for intent in intents:
			for query in queries:
				print("%s = %s" % (userStrategy[intent][query], solver.get_value(userStrategy[intent][query])))

		for query in queries:
			for tup in tuples:
				print("%s = %s" % (dbmsStrategy[query][tup], solver.get_value(dbmsStrategy[query][tup])))

def findNashEquilibria(intents, queries, tuples, matches, strict, minReward, minRewardValue):
	userStrategy = dict()
	dbmsStrategy = dict()
	nashUserStrategy = dict()
	nashdbmsStrategy = dict()
	rewardMatrix = constructRewardMatrix(intents, tuples, matches)
	letters = set()
	nashRestrictions = list()

	#User Strategy matrix, each cell holds a variable for the SMT
	for intent in intents:
		if intent not in userStrategy:
			userStrategy[intent] = dict()
		for query in queries:
			userStrategy[intent][query] = Symbol('User['+intent + '][' + query + ']', REAL)
			letters.add(userStrategy[intent][query])
			
	#DBMS Strategy matrix, each cell holds a variable for the SMT
	for query in queries:
		if query not in dbmsStrategy:
			dbmsStrategy[query] = dict()
		for tup in tuples:
			dbmsStrategy[query][tup] = Symbol('DBMS['+query + '][' + tup + ']', REAL)
			letters.add(dbmsStrategy[query][tup])
	
	#We create a strategy for each move that can be made from the current position
	#This means that only a single row changes, the rest of the rows are the same as the strategies above
	#There also needs to be a strategy for each cell and a restriction only on the cell that this strategy belongs to
	for intent in intents:
		nashUserStrategy[intent] = dict()
		for query in queries:
			nashUserStrategy[intent][query] = copy.deepcopy(userStrategy)
			for query2 in copy.deepcopy(queries):
				nashUserStrategy[intent][query][intent][query2] = Symbol('Nash'+str(len(nashUserStrategy))+str(len(nashUserStrategy[intent]))+'User['+intent + '][' + query2 + ']', REAL)
				letters.add(nashUserStrategy[intent][query][intent][query2])
				if query == query2:
					nashRestrictions.append(NotEquals(nashUserStrategy[intent][query][intent][query2], userStrategy[intent][query2]))

	#Same here except for DBMS
	for query in queries:
		nashdbmsStrategy[query] = dict()
		for tup in tuples:
			nashdbmsStrategy[query][tup] = copy.deepcopy(dbmsStrategy)
			for tup2 in tuples:
				nashdbmsStrategy[query][tup][query][tup2] = Symbol('Nash'+str(len(nashdbmsStrategy))+str(len(nashdbmsStrategy[query]))+'DBMS['+query + '][' + tup2 + ']', REAL)
				letters.add(nashdbmsStrategy[query][tup][query][tup2])
				if tup == tup2:
					nashRestrictions.append(NotEquals(nashdbmsStrategy[query][tup][query][tup2], dbmsStrategy[query][tup2]))

	#Tells the range of values, for now set to Pure strategy so [0,1]
	domains = And([Or(Equals(l, Real(0)), Equals(l, Real(1))) for l in letters])
	if DEBUG:
		print('\nDomain Serialization: ')	
		print(domains)

	#Adds restriction that no value from the nashStrategies can be the same as the corresponding cell they are testing. This ensures a 'move'
	nashProblem = And(nashRestrictions)
	if DEBUG:
		print('\nNash Domain Serialization: ')
		print(nashProblem)

	#This is doing all the row stochastic stuff
	allEquals = []
	#Adds each row of the user strategy
	stochasticMatrixUser = list()
	stochasticMatrixNashUser = list()
	for intent in intents:
		stochasticMatrixUser.append(Plus(userStrategy[intent].values()))
		for query in queries:
			allEquals.append(Equals(Plus(nashUserStrategy[intent][query][intent].values()), Real(1)))
			
	#Adds each row of the DBMS strategy
	stochasticMatrixdbms = list()
	stochasticMatrixNashdbms = list()
	for query in queries:
		stochasticMatrixdbms.append(Plus(dbmsStrategy[query].values()))
		for tup in tuples:
			allEquals.append(Equals(Plus(nashdbmsStrategy[query][tup][query].values()), Real(1)))
	
	#Checks the rows to make sure that the strategies are row stochastic
	stochUserEquals = [Equals(x, Real(1)) for x in stochasticMatrixUser]
	stochdbmsEquals = [Equals(x, Real(1)) for x in stochasticMatrixdbms]
	allEquals += stochUserEquals + stochdbmsEquals

	#Stochastic problem
	stochasticProblem = And(set(allEquals))
	if DEBUG:
		print('\nStochastic Serialization: ')
		print(stochasticProblem.serialize())
	
	
	
	#Uses Formula 1 from my paper to calculate the payoff, assuming uniform prior.
	reward = list()
	for intent in intents:
		for query in queries:
			for tup in tuples:
				reward.append(Times(Real(1/len(intents)), userStrategy[intent][query], dbmsStrategy[query][tup], rewardMatrix[intent][tup]))

	#Reward problem, requires a minimum reward. May not always be possible to achieve this reward
	rewardProblem = GE(Plus(reward), Real(minRewardValue))
	if DEBUG:
		print('\nReward Serialization: ')	
		print(rewardProblem)

	nashRewardUser = dict()
	nashRewardDbms = dict()

	#Again using Formula 1, but now we are creating one for each move to make sure that it is less than (Strict Nash) or less than or equal (Nash)
	for strat in nashUserStrategy:
		if strat not in nashRewardUser:
			nashRewardUser[strat] = dict()
		for strat2 in nashUserStrategy[strat]:
			if strat2 not in nashRewardUser[strat]:
				nashRewardUser[strat][strat2] = list()
			for intent in intents:
				for query in queries:
					for tup in tuples:
						nashRewardUser[strat][strat2].append(Times(Real(1/len(intents)), nashUserStrategy[strat][strat2][intent][query], dbmsStrategy[query][tup], rewardMatrix[intent][tup]))

	#Same, but for DBMS side. Just separated them to make it cleaner
	for strat in nashdbmsStrategy:
		if strat not in nashRewardDbms:
			nashRewardDbms[strat] = dict()
		for strat2 in nashdbmsStrategy[strat]:
			if strat2 not in nashRewardDbms[strat]:
				nashRewardDbms[strat][strat2] = list()
			for intent in intents:
				for query in queries:
					for tup in tuples:
						nashRewardDbms[strat][strat2].append(Times(Real(1/len(intents)), userStrategy[intent][query], nashdbmsStrategy[strat][strat2][query][tup], rewardMatrix[intent][tup]))

	if DEBUG:
		print('\nReward Serialization Nash: ')
	
	#Check user nash
	#This is where we actually perform the checking to see if it is less than or equal (or prep to be added to the solver)
	userNash = list()
	for intent in intents:
		for query in queries:
			if strict:
				userNash.append(Implies(NotEquals(nashUserStrategy[intent][query][intent][query], userStrategy[intent][query]), LT(Plus(nashRewardUser[intent][query]), Plus(reward))))
			else:
				userNash.append(Implies(NotEquals(nashUserStrategy[intent][query][intent][query], userStrategy[intent][query]), LE(Plus(nashRewardUser[intent][query]), Plus(reward))))
						
	userNashProblem = And(userNash)

	if DEBUG:
		print(userNashProblem.serialize())

	#Check dbms nash
	dbmsNash = list()
	for query in queries:
		for tup in tuples:
			if strict:
				dbmsNash.append(Implies(NotEquals(dbmsStrategy[query][tup], nashdbmsStrategy[query][tup][query][tup]), LE(Plus(nashRewardDbms[query][tup]), Plus(reward))))
			else:
				dbmsNash.append(Implies(NotEquals(dbmsStrategy[query][tup], nashdbmsStrategy[query][tup][query][tup]), LE(Plus(nashRewardDbms[query][tup]), Plus(reward))))

	dbmsNashProblem = And(dbmsNash)

	if DEBUG:
		print(dbmsNashProblem.serialize())

	#Add each component to the solver and test as we go
	#PySMT has another method where you just AND everything together, but they suggest
	#this method as it looks cleaner and you can see which one fails, if any
	with Solver(name="z3") as solver:
		solver.add_assertion(domains)
		if not solver.solve():
			print('No solultion available (domains)')
			return
		print('Can satisfy domains')

		solver.add_assertion(nashProblem)
		if not solver.solve():
			print('No solultion available (nash restrictions)')
			return
		print('Can satisfy nash domains')
		
		solver.add_assertion(stochasticProblem)
		if not solver.solve():
			print('No sulution available (stochastic)')
			return
		print('Can satisfy stochastic')
		
		if minReward:
			solver.add_assertion(rewardProblem)
			if not solver.solve():
				print('No solution available')
				return
			print('Can satisfy minimum reward')
		
		solver.add_assertion(userNashProblem)
		if not solver.solve():
			print('No solution available (user nash)')
			return

		print('Can satisfy user nash')

		solver.add_assertion(dbmsNashProblem)
		if not solver.solve():
			print('No solution available (dbms nash)')
			return
		print('Can satisfy dbms nash')

		#Print out the final assignments if it made it this far, as a solution exists
		for intent in intents:
			for query in queries:
				print("%s = %s" % (userStrategy[intent][query], solver.get_value(userStrategy[intent][query])))

		for query in queries:
			for tup in tuples:
				print("%s = %s" % (dbmsStrategy[query][tup], solver.get_value(dbmsStrategy[query][tup])))

def main():
	#General Notes:
	#	Intents   			(Parameter 1): What the user is looking for
	#	Queries   			(Parameter 2): How the user can express the intent
	#	Tuples    			(Parameter 3): How the dbms can respond
	#	Matches   			(Parameter 4): List of tuples indicating which ones match
	#	Strict    			(Parameter 5): True for strict Nash (may not find one), False for Nash (should always find one, even if it's stupid)
	#	MinReward 			(Parameter 6): True to try and generate a strategy where the minimum reward is satisfied (may not always find one) Range 0-1
	#	Min Reward Value 	(Parameter 7): Minimum reward value, min=0 max=1. 
		
	#Currently:
	#	Strict: 			True
	#	Min Reward: 		False
	#	Min Reward Value: 	1

	#I am feeling crazy mode (used numbers to make it easier to map)
	#WARNING, strict nash does not exist for this one (not enough signals, so it's easy for user or dbms to change and get same reward)
	#WARNING 2, takes a few seconds to run...
	# intents = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10']
	# queries = ['x', 'y', 'z', 'a', 'b']
	# tuples = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10']
	# matches = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')]

	#Too many possible answers
	# intents = ['apple', 'orange']
	# queries = ['a', 'x']
	# tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
	# matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]

	#More then one correct answer
	# intents = ['apple', 'orange']
	# queries = ['a', 'x']
	# tuples = ['apple gross', 'orange tasty', 'apple oh boy!']
	# matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('apple', 'apple oh boy!')]

	# Not enough signals
	# intents = ['apple', 'orange', 'plum']
	# queries = ['a', 'x']
	# tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
	# matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]
	
	# Normal 3
	# intents = ['apple', 'orange', 'plum']
	# queries = ['x', 'y', 'z']
	# tuples = ['apple gross', 'orange tasty', 'plum oh boy!']
	# matches = [('apple', 'apple gross'), ('orange', 'orange tasty'), ('plum', 'plum oh boy!')]
	
	# Normal 2
	# intents = ['apple', 'orange']
	# queries = ['x', 'y']
	# tuples = ['apple gross', 'orange tasty']
	# matches = [('apple', 'apple gross'), ('orange', 'orange tasty')]
	
	#From Paper 
	intents = ['CS', 'EE']
	queries = ['x', 'y']
	tuples = ['CS517', 'EE433']
	matches = [('CS', 'CS517'), ('EE', 'EE433')]

	findNashEquilibria(intents, queries, tuples, matches, True, False, 1)
	
	#Feel free to call just the min reward too. 
	#Be warned, if you use an odd number of intents it probably won't return anything
	#PySMT likes to convert the fractions into insanely huge numerators and denominators
	#minReward(intents, queries, tuples, matches, 1)

if __name__ == '__main__':
	main()