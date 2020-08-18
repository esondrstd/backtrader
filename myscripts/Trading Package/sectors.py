import itertools 
from collections import defaultdict

mylist1 = ('AAPL','MSFT','INTC','POOP')
mylist2 = ('FB','BADU','AMAT')
mylist3 = ('WM','ERIK')

list1 = list(itertools.combinations(mylist1, 2)) 
list2 = list(itertools.combinations(mylist2, 2))
list3 = list(itertools.combinations(mylist3, 2))

adf_dict = defaultdict(list)

for (a, b, c) in itertools.zip_longest(list1, list2, list3):
	for i in (a,b,c):
		if i is not None:
			t1 = i[0]
			t2 = i[-1]
			name = f'{t1}/{t2}'
			print(name)
			adf_dict[f'{name}'].append(True)
			

print(adf_dict)
