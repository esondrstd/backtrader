"""
    The point of entry and exit are different in a Queue.
    Enqueue - Adding an element to a Queue
    Dequeue - Removing an element from a Queue
    Random access is not allowed - you cannot add or remove an element from the middle.
    
    Elements are added from the end and removed at the beginning of the Queue.
    Treat lists like arrays (fixed in size) - we can achieve it by virtually restricting the size of the list. This is done by ensuring that the list doesn't grow beyond a fixed limit or size.
    Use a Tail pointer to keep a tab of the elements added to the Queue - the Tail pointer will always point to the next available space. For instance when there are three elements in the queue, Tail will point to the fourth place. When the queue is full, the tail pointer will be greater than the declared size.
    Use a Head pointer to keep a tab on the elements removed from the Queue - the Head pointer will point to the element to be dequeued next. For instance, if there are three elements in a queue, the Head pointer will be pointing to the first element. After one dequeue operation, the Head pointer will point to the second element in the queue. No element will be actually removed from the queue. This is because once an element is removed, the list automatically shifts all the other elements by one position to the left. This means that the position 0 will always contain an element, which is not how an actual queue works.
    Use a Reset method - this method is called to reset the queue, Tail and Head. For instance, if there are three elements in the queue then Head = 0, Tail = 4. Now, if we dequeue all three elements, the queue will be empty meaning Head = Tail = 4. So if you enqueue an element, it will happen at position 4 which is not correct. Hence it becomes necessary to reset these pointers to 0. Note that since we are not actually deleting elements, the list still contains the 'deleted" elements, hence a new list needs to be created as well.
"""
import queue
from collections import defaultdict


class Queue:

  #Constructor creates a list
  def __init__(self):
      self.queue = list()

  #Adding elements to queue
  def enqueue(self,data):
      #Checking to avoid duplicate entry (not mandatory)
      if data not in self.queue:
          self.queue.insert(0,data)
          return True
      return False

  #Removing the last element from the queue
  def dequeue(self):
      if len(self.queue)>0:
          return self.queue.pop()
      return ("Queue Empty!")

  #Getting the size of the queue
  def size(self):
      return len(self.queue)

  #printing the elements of the queue
  def printQueue(self):
      return self.queue





myQueue = Queue()
print(myQueue.enqueue(5)) #prints True
print(myQueue.enqueue(6)) #prints True
print(myQueue.enqueue(9)) #prints True
print(myQueue.enqueue(5)) #prints False
print(myQueue.enqueue(3)) #prints True
print(myQueue.size())     #prints 4
print(myQueue.dequeue())  #prints 5
print(myQueue.dequeue())  #prints 6
print(myQueue.dequeue())  #prints 9
print(myQueue.dequeue())  #prints 3
print(myQueue.size())     #prints 0
print(myQueue.dequeue())  #prints Queue Empty!







"""
class Queue:

    #Constructor
    def __init__(self):
        self.queue = list()
        self.maxSize = 8
        self.head = 0
        self.tail = 0

    #Adding elements
    def enqueue(self,data):
        #Checking if the queue is full
        if self.size() >= self.maxSize:
            return ("Queue Full")
        self.queue.append(data)
        self.tail += 1
        return True     

    #Deleting elements 
    def dequeue(self):
        #Checking if the queue is empty
        if self.size() <= 0:
            self.resetQueue()
            return ("Queue Empty") 
        data = self.queue[self.head]
        self.head+=1
        return data
                
    #Calculate size
    def size(self):
        return self.tail - self.head
    
    #Reset queue
    def resetQueue(self):
        self.tail = 0
        self.head = 0
        self.queue = list()
    
q = Queue()
print(q.enqueue(1))#prints True
print(q.enqueue(2))#prints True
print(q.enqueue(3))#prints True
print(q.enqueue(4))#prints True
print(q.enqueue(5))#prints True
print(q.enqueue(6))#prints True
print(q.enqueue(7))#prints True
print(q.enqueue(8))#prints True
print(q.enqueue(9))#prints Queue Full!
print(q.size())#prints 8        
print(q.dequeue())#prints 8
print(q.dequeue())#prints 7 
print(q.dequeue())#prints 6
print(q.dequeue())#prints 5
print(q.dequeue())#prints 4
print(q.dequeue())#prints 3
print(q.dequeue())#prints 2
print(q.dequeue())#prints 1
print(q.dequeue())#prints Queue Empty
#Queue is reset here 
print(q.enqueue(1))#prints True
print(q.enqueue(2))#prints True
print(q.enqueue(3))#prints True
print(q.enqueue(4))#prints True
"""



ages = {'billy':16,'anna':17,'joe':15,'kelly':19}

newages = sorted(ages.items(),key=lambda x:x[1])  #Now a list.  Key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.

print(ages)
print(newages)

newages_dict = {k: v for k,v in sorted(ages.items(),key=lambda x:x[1])}  #Need to convert back to dictionary.  k=key, v=value in key/value pair
print(newages_dict)
print(newages_dict.keys())

#*********************************************************************************************

#nested_dict = { 'dictA': {'key_1': 'value_1'},'dictB': {'key_2': 'value_2'}}

stocks = {'SPY':{'obv':10},'XHB':{'obv': 5},'XLT':{'obv': 8}}
print(stocks)

res = sorted(stocks.items(), key = lambda x: x[1]['obv']) 
print(res)

res_dict = {k: v for k,v in sorted(stocks.items(),key=lambda x: x[1]['obv'])}  #Need to convert back to dictionary.  k=key, v=value in key/value pair
print(res_dict)
print(res_dict.keys())
