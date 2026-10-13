class MinHeap:

    def __init__(self):
        self.data = []

    def size(self):
        return len(self.data)

    def peek_score(self):
        return self.data[0][0]

    def push(self, score, payload):
        self.data.append((score, payload))
        self._sift_up(len(self.data) - 1)

    def pop_min(self):
        smallest = self.data[0]
        last = self.data.pop()
        if self.data:
            self.data[0] = last
            self._sift_down(0)
        return smallest

    def _swap(self, i, j):
        self.data[i], self.data[j] = self.data[j], self.data[i]

    def _sift_up(self, i):
        while i > 0:
            parent = (i -1) // 2
            if self.data[i][0] < self.data[parent][0]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        p = len(self.data)
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2
            if left < p and self.data[left][0] < self.data[smallest][0]:
                smallest = left
            if right < p and self.data[right][0] < self.data[smallest][0]:
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    def top_k(rows, k, score_of):
        heap = MinHeap()
        for row in rows:
            score = score_of(row)
            if heap.size() < k:
                heap.push(score, row)
            elif score > heap.peek_score():
                heap.pop_min()
                heap.push(score, row)
            ascending = []

            while heap.size() > 0:
                ascending.append(heap.pop_min()[1])
                ascending.reverse()
                return ascending




  