from random import shuffle

class Decks:
	def __init__(self):
		answerFile = open('answers', 'r')
		questionFile = open('questions', 'r')
		self.answers = []
		for a in answerFile:
			self.answers.append(a.strip())
		answerFile.close()
		self.questions = []
		for q in questionFile:
			self.questions.append(q.strip())
		questionFile.close()

		shuffle(self.answers)
		shuffle(self.questions)

	def getAnswer(self):
		if self.answers:
			return self.answers.pop()

	def getQuestion(self):
		if self.questions:
			return self.questions.pop()
