from random import randint

trials = 1_000_000
contains_0 = 0
contains_1 = 0
contains_2 = 0
contains_3 = 0

for _ in range(trials):
	selection = []
	for _ in range(20):
		selected = randint(1, 675)
		while selected in selection:
			selected = randint(1, 675)
		selection.append(selected)
	contains = (1 in selection) + (2 in selection) + (3 in selection)
	if contains == 0:
		contains_0 += 1
	elif contains == 1:
		contains_1 += 1
	elif contains == 2:
		contains_2 += 1
	elif contains == 3:
		contains_3 += 1

print(f'contains 0:', {100 * contains_0 / trials})
print(f'contains 1:', {100 * contains_1 / trials})
print(f'contains 2:', {100 * contains_2 / trials})
print(f'contains 3:', {100 * contains_3 / trials})