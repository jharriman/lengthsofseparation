#! /usr/bin/env python
import sys
import copy
import numpy as np

# Utils
def interval_dist(i_tuple):
    return i_tuple[1] - i_tuple[0]

def lerp(l, h, w):
    return (1-w) * l + w * h

class ArithmeticEncoder(object):
    def __init__(self, dictFile):
        # Open the dx1 file for writing
        with open(dictFile, "r") as f:
            lines = f.readlines()
        
        # Generate the frequency, word_list, alphabet and the empirical probabilities of the letters
        print "Generating word frequencies and finding phonemes . . ."
        frequency, word_list, word_phonemes = self.letters_and_frequencies(lines)
        alphabet = sorted(frequency.keys())
        tot_letters = sum(frequency.values())
        probabilities = dict(map(lambda (k,v): (k, float(v)/tot_letters), frequency.iteritems()))

        # Since we are using the unigram model, the interval widths can be precomputed (to an extent)
        # After trying this I've discovered that I realy should only be doing one interval
        # But we save time by keeping a record of every interval that we generate
        levels = 1
        self.intervals, self.interval_widths = self.create_intervals(alphabet, probabilities, levels)

        # Create reverse intervals for decoding, removing the trace.
        self.reverseIntervals = {v: k for k, v in self.intervals.items() if k != "trace"}


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
        go = True
        while(go):
            # TODO! This is horribly inefficient, should use a different structure
            # to contain this information
            for key in self.reverseIntervals.keys():
                # Scale the key to this interval
                lerpedKey = lerp(range[0], range[1], key[0]), lerp(range[0], range[1], key[1])
                # Check if the keys are equivalent
                if number > lerpedKey[0] and number <= lerpedKey[1]:
                    letter = self.reverseIntervals[key]
                    if letter == "#":
                        go = False
                        break
                    word.append(self.reverseIntervals[key])
                    range = lerpedKey
        return "".join(word)


    def create_intervals(self, alphabet, probs, depth):
        intervals = dict()
        # find the interval widths for each letter
        # [c(i), c(i) + p(li))
        prev_ci = 0
        for letter in alphabet:
            intervals[letter] = probs[letter] + prev_ci

        # Remove hash from the alphabet so that gen_intervals can add it at the /end/ of our intervals, as per the course notes
        alphabet.remove("#")

        # Generate layers of dictionaries up to the maximum depth for the corpus
        prev_width = 1
        prev_layer = dict()
        layers = self.gen_intervals(1.0, 0.0, 1.0, alphabet, intervals, depth)

        # Add the hash back
        alphabet.append("#")
        return layers, intervals

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
        # Check if the lines have a phonemic representation at the end
        line = lines[0]
        segments = line.split()
        symbols = dict()

        # Maintain a word_list and a list of phonemes for each word
        word_list = list()
        word_phonemes = dict()

        if len(segments) >= 3: # The phonemic representation is present so we accept this
            for line in lines:
                segments = line.split()
                word = segments[0]
                if "#" not in word:
                    word += "#"
                word_list.append(word)
                sym_list = list()
                for i in range(2, len(segments)):
                    symbol = segments[i]
                    sym_list.append(symbol)
                    symbols[symbol] = symbols.get(symbol, 0) + 1
                if "#" not in segments:
                    sym_list.append("#")
                    symbols["#"] = symbols.get("#", 0) + 1
                word_phonemes[word] = sym_list
        else: # The phonemes aren't present, use the letters
            for line in lines:
                segments = line.split()
                word = segments[0]
                if "#" not in word:
                    word += "#"
                word_list.append(word)
                let_list = list()
                for letter in word:
                    let_list.append(letter)
                    symbols[letter] = symbols.get(letter, 0) + 1
                word_phonemes[word] = let_list
        return symbols, word_list, word_phonemes
