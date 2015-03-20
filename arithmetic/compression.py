# Copyright 2015 GNU GPL
import sys
import copy
import numpy as np

# Utils
def interval_dist(i_tuple):
    return i_tuple[1] - i_tuple[0]

def lerp(l, h, w):
    return (1-w) * l + w * h

class ArithmeticEncoder(object):
    def __init__(self, dictionaryLines):
        if (type(dictionaryLines) == str):
            # Open the word list for reading
            with open(dictionaryLines, "r") as f:
                lines = f.readlines()
        else:
            lines = dictionaryLines

        # Generate the frequency, word_list, alphabet and the empirical probabilities of the letters
        frequency, word_list = self.letters_and_frequencies(lines)
        self.alphabet = sorted(frequency.keys())
        tot_letters = sum(frequency.values())
        probabilities = dict(map(lambda (k,v): (k, float(v)/tot_letters), frequency.iteritems()))

        # Generate the intervals
        levels = 1
        self.intervals = self.create_intervals(self.alphabet, probabilities, levels)

        # Create reverse intervals for decoding, removing the trace.
        self.reverseIntervals = {v: k for k, v in self.intervals.items() if k != "trace"}

    def encodePhrase(self, string):
        words = string.split()
        return [self.encode(x) for x in words]

    def decodeSet(self, numbers):
        return " ".join([self.decode(x) for x in numbers])

    def encode(self, word):
        letters = list(word)
        # Add a word end symbol, if not already present
        if letters[-1] != "#":
            letters.append("#")

        # Initial range
        range = (0, 1)
        for ell in letters:
            # Find ell in our interval range
            l, u = self.intervals[ell]
            range = lerp(range[0], range[1], l), lerp(range[0], range[1], u)

        # Once we've reached the end of word character, we don't much care about
        # the range, so jut take the middle of this interval.
        return sum(range) / 2

    def decode(self, number):
        word = list()
        range = (0,1)
        while(True):
            # TODO! This is horribly inefficient, should use a different structure
            # to contain this information
            for key in self.reverseIntervals.keys():
                # Scale the key to this interval
                lerpedKey = lerp(range[0], range[1], key[0]), lerp(range[0], range[1], key[1])
                # Check if the keys are equivalent
                if number > lerpedKey[0] and number <= lerpedKey[1]:
                    letter = self.reverseIntervals[key]
                    if letter == "#":
                        return "".join(word)
                        break
                    word.append(self.reverseIntervals[key])
                    range = lerpedKey

    def create_intervals(self, alphabet, probs, depth):
        intervals = dict()
        # find the interval widths for each letter
        # [c(i), c(i) + p(li))
        prev_ci = 0
        for letter in alphabet:
            intervals[letter] = probs[letter] + prev_ci

        # Remove hash from the alphabet so that gen_intervals can add it at the
        # the end of the interval (end of word characters must be treated differently)
        alphabet.remove("#")

        # Generate layers of dictionaries up to the maximum depth for the corpus
        prev_width = 1
        prev_layer = dict()
        layers = self.gen_intervals(1.0, 0.0, 1.0, alphabet, intervals, depth)

        # Add the hash back
        alphabet.append("#")
        return layers

    def gen_intervals(self, width, start, end, letters, interval_width, depth):
        new_interval = dict()
        # Base case
        if (depth == 1):
            new_start = start
            for letter in letters:
                new_end = new_start + interval_width[letter] * width
                new_interval[letter] = (new_start, new_end)
                new_start = new_end
            # Take care of the hash interval
            # end += interval_width["#"] * width
            new_interval["#"] = (new_start, end)
            new_interval["trace"] = (start, end)
        else:
            new_start = start
            # Recursive case
            for letter in letters:
                new_end = new_start + interval_width[letter] * width
                new_interval[letter] = self.gen_intervals(interval_width[letter] * width, new_start, new_end,
                                                          letters, interval_width, depth - 1)
                new_start = new_end
            # Take care of the hash interval
            # end += interval_width["#"] * width
            new_interval["#"] = (new_start, end)
            new_interval["trace"] = (start, end)
        return new_interval

    def letters_and_frequencies(self, lines):
        symbols = {}
        # Maintain a word_list and a list of phonemes for each word
        word_list = []
        for line in lines:
            segments = line.split()
            word = segments[0]
            # Need an end of line break, if its not already part of the word.
            if "#" not in word:
                word += "#"
            word_list.append(word)
            let_list = list()
            for letter in word:
                let_list.append(letter)
                symbols[letter] = symbols.get(letter, 0) + 1
        return symbols, word_list
