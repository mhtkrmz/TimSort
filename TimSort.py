# Description:
# This file contains an advanced version of the Timsort sorting algorithm.
# It starts by splitting a list into segments of increasing, decreasing, or unsorted elements.
# Then, it processes these segments by sorting the unsorted ones and reversing the decreasing ones.
# Finally, it merges these segments into a single sorted list.

# Constants for segment types
Inc, Dec, Unsorted = +1, -1, 0

# Thresholds for run lengths
runThreshold = 32
blockMin = 32
blockMax = 63  # Note: blockMax >= blockMin*2+1 is required

class Segment:
    """Represents a segment within a list."""
    def __init__(self, start, end, tag):
        self.start = start
        self.end = end
        self.tag = tag

    def len(self):
        """Returns the length of the segment."""
        return self.end - self.start

    def __repr__(self):
        """String representation of the segment."""
        return f'Segment({self.start},{self.end},{self.tag})'

class IncDecRuns:
    """Identifies increasing and decreasing segments within a list."""
    def __init__(self, L, key=lambda x: x):
        self.L = L
        self.key = key
        self.m = len(L) - 1
        self.dir = Inc if key(L[1]) >= key(L[0]) else Dec
        self.i = 0  # most recent segment boundary
        self.j = 0  # position reached

    def next(self):
        """Returns the next segment or None if the end of the list is reached."""
        if self.j == self.m:
            return None
        self.i = self.j
        while self.j < self.m and (
            (self.dir == Inc and self.key(self.L[self.j]) <= self.key(self.L[self.j+1])) or
            (self.dir == Dec and self.key(self.L[self.j]) >= self.key(self.L[self.j+1]))
        ):
            self.j += 1
        if self.j == self.m:
            return Segment(self.i, self.m+1, self.dir)
        else:
            self.dir = -self.dir
            return Segment(self.i, self.j, -self.dir)

    def finished(self):
        """Checks if the end of the list has been reached."""
        return self.j == self.m

class FuseSegments:
    """Fuses consecutive short segments into longer unsorted ones."""
    def __init__(self, IncDecRuns):
        self.IDR = IncDecRuns
        self.next1 = self.IDR.next()
        self.next2 = self.IDR.next()

    def next(self):
        """Returns the next fused segment, or None if finished."""
        if not self.next2:
            curr, self.next1 = self.next1, None
            return curr
        if self.next1.len() < runThreshold and self.next2.len() < runThreshold:
            start = self.next1.start
            while self.next2.len() < runThreshold and not self.IDR.finished():
                self.next2 = self.IDR.next()
            end = self.next2.end if self.next2.len() < runThreshold else self.next2.start
            self.next1 = None if self.next2.len() < runThreshold else self.next2
            self.next2 = None if self.next2.len() < runThreshold else self.IDR.next()
            return Segment(start, end, Unsorted)
        else:
            curr, self.next1 = self.next1, self.next2
            self.next2 = self.IDR.next()
            return curr

    def finished(self):
        """Checks if there are no more segments to fuse."""
        return not self.next1

def segments(L):
    """Splits the list into manageable segments for sorting."""
    FS = FuseSegments(IncDecRuns(L))
    S, curr = [], FS.next()
    while curr:
        if curr.len() == 1 and S and not FS.finished():
            S[-1].end += 1
        elif curr.tag != Unsorted or curr.len() <= blockMax:
            S.append(curr)
        else:
            start, n = curr.start, curr.len()
            k, divs = n // blockMin, [start + (n*i) // k for i in range(k+1)]
            S.extend(Segment(divs[i], divs[i+1], 0) for i in range(k))
        curr = FS.next()
    return S

def insertSort(L, start, end, key=lambda x: x):
    """Sorts a segment of the list using insertion sort."""
    for i in range(start, end):
        item, j = L[i], i - 1
        while j >= start and key(L[j]) > key(item):
            L[j + 1] = L[j]
            j -= 1
        L[j + 1] = item

def reverse(L, start, end):
    """Reverses a segment of the list."""
    L[start:end] = reversed(L[start:end])

def processSegments(L, segs, key=lambda x: x):
    """Processes each segment - sorts unsorted ones and reverses decreasing ones."""
    for seg in segs:
        if seg.tag == Unsorted:
            insertSort(L, seg.start, seg.end, key)
        elif seg.tag == Dec:
            reverse(L, seg.start, seg.end)

def mergeSegments(L, seg1, seg2, M, start, key=lambda x: x):
    """Merges two segments together in sorted order."""
    i, j, k, size = 0, 0, 0, 0
    while i < seg1.len() and j < seg2.len():
        if key(L[seg1.start + i]) <= key(L[seg2.start + j]):
            M[start + k] = L[seg1.start + i]
            i += 1
        else:
            M[start + k] = L[seg2.start + j]
            j += 1
        k += 1
        size += 1
    while i < seg1.len():
        M[start + k] = L[seg1.start + i]
        i, k, size = i + 1, k + 1, size + 1
    while j < seg2.len():
        M[start + k] = L[seg2.start + j]
        j, k, size = j + 1, k + 1, size + 1
    return size

def copySegment(L, seg, M, start):
    """Copies a segment from L to M."""
    for i in range(seg.len()):
        M[start + i] = L[seg.start + i]
    return seg.len()

def mergeRound(L, segs, M, key=lambda x: x):
    """Merges segments in rounds to sort the list."""
    mergedSegs, i = [], 0
    while i < len(segs) - 1:
        mergeSegments(L, segs[i], segs[i + 1], M, len(mergedSegs), key)
        mergedSegs.append(Segment(segs[i].start, segs[i + 1].end, Inc))
        i += 2
    if len(segs) % 2 == 1:
        mergedSegs.append(segs[-1])
        copySegment(L, segs[-1], M, len(mergedSegs) - 1)
    return mergedSegs

def mergeRounds(L, segs, M, key=lambda x: x):
    """Performs multiple rounds of merging until the list is fully sorted."""
    while len(segs) > 1:
        segs = mergeRound(L, segs, M, key)
        L[:], M[:] = M[:], L[:]
    return L

def SimpleTimSort(L, key=lambda x: x):
    """Main function to sort a list using a simplified version of Timsort."""
    if len(L) <= 1:
        return L
    segs = segments(L)
    processSegments(L, segs, key)
    M = [None] * len(L)
    return mergeRounds(L, segs, M, key)

# Testing the advanced Timsort implementation
l1 = [1, 5, 7, 3, 9, 2, 4, 6, 8, 9, 345, 46, 57, 2, 34, 658, 7567]
print(SimpleTimSort(l1))

l2 = [[1, 3, 5], [2], [3, 5, 5, 7, 8, 3], [5345, 75, [34, 5]], [3, 2, 4], [5, 6, 1], [1, 1, 1, 1]]

testl2 = [3, 4, 5, 6, 7, 5, 6, 7, 8, 5, 4, 6, 4, 3, 2, 1, 2, 3, 2, 1, 2, 3, 2, 1, 2, 3]
print(SimpleTimSort(testl2))
