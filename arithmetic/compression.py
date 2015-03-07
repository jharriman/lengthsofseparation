#! /usr/bin/env python
import sys
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import *

def interval_dist(i_tuple):
    return i_tuple[1] - i_tuple[0]

def create_intervals(alphabet, probs, depth):
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
    layers = gen_intervals(1.0, 0.0, 1.0, alphabet, intervals, depth)

    # Add the hash back
    alphabet.append("#")
    return layers, intervals

def gen_intervals(width, start, end, letters, interval_width, depth):
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
            new_interval[letter] = gen_intervals(interval_width[letter] * width, new_start, new_end, 
                                                 letters, interval_width, depth - 1)
            new_start = new_end
        # Take care of the hash interval
        # end += interval_width["#"] * width
        new_interval["#"] = (new_start, end)
        new_interval["trace"] = (start, end)
    return new_interval

def map_left_to_right(words, word_phonemes, intervals, letters, interval_width):
    word_intervals = dict()
    for word in words:
        symbols = word_phonemes[word]
        symbols.remove("#")
        cur_dict = intervals
        for sym in symbols:
            cur_dict = cur_dict[sym]
            if isinstance(cur_dict, tuple): # generate another level
                letters.remove("#")
                cur_dict = gen_single_interval(interval_dist(cur_dict), cur_dict[0], cur_dict[1], letters, interval_width)
                letters.append("#")                
        word_intervals[word] = cur_dict["#"]
        symbols.append("#")
    return word_intervals

def map_right_to_left(words, word_phonemes, intervals, letters, interval_width):
    word_intervals = dict()
    for word in words:
        symbols = word_phonemes[word]
        symbols.remove("#")
        symbols.reverse()
        cur_dict = intervals
        for sym in symbols:
            cur_dict = cur_dict[sym]
            if isinstance(cur_dict, tuple): # generate another level
                letters.remove("#")
                cur_dict = gen_single_interval(interval_dist(cur_dict), cur_dict[0], cur_dict[1], letters, interval_width)
                letters.append("#")                
        word_intervals[word] = cur_dict["#"]
        symbols.append("#")
    return word_intervals
    
def letters_and_frequencies(lines):
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

def debug_data():
    alphabet = ["a", "e", "i", "o", "u", "#"]
    probabilities = { "a" : 0.2,
                      "e" : 0.3,
                      "i" : 0.1,
                      "o" : 0.2,
                      "u" : 0.1,
                      "#" : 0.1 }
    word_list = ["eaii#"]
    phonemes = { "eaii#" : ["e", "a", "i", "i", "#"] }
    return alphabet, probabilities, word_list, phonemes

# Debugging code borrowed from StackOverflow http://stackoverflow.com/questions/3229419/pretty-printing-nested-dictionaries-in-python
def pretty(d, indent=0):
   for key, value in d.iteritems():
      print '\t' * indent + str(key)
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print '\t' * (indent+1) + str(value)

if __name__ == "__main__":
    # Open the dx1 file for writing
    f = open(sys.argv[1], "r")
    lines = f.readlines()

    # (Optional) open the storage location for our data
    if len(sys.argv) > 2:
        g = open(sys.argv[2], "w+")

    # Generate the frequency, word_list, alphabet and the empirical probabilities of the letters
    print "Generating word frequencies and finding phonemes . . ."
    frequency, word_list, word_phonemes = letters_and_frequencies(lines)
    alphabet = sorted(frequency.keys())
    tot_letters = sum(frequency.values())
    probabilities = dict(map(lambda (k,v): (k, float(v)/tot_letters), frequency.iteritems()))

    # DEBUG: If not commented, we use the example data provided in the course notes
    #alphabet, probabilities, word_list, word_phonemes = debug_data()

    # Since we are using the unigram model, the interval widths can be precomputed (to an extent)
    # After trying this I've discovered that I realy should only be doing one interval
    # But we save time by keeping a record of every interval that we generate
    levels = 1
    intervals, interval_widths = create_intervals(alphabet, probabilities, levels)

    # Find left to right intervals
    print "Mapping words left to right . . ."
    l_to_r = map_left_to_right(word_list, word_phonemes, intervals, alphabet, interval_widths)

    # Find right to left intervals
    print "Mapping words right to left . . ."
    r_to_l = map_right_to_left(word_list, word_phonemes, intervals, alphabet, interval_widths)

    # Print words to stdout
    print "Begin interval output"
    word_list = sorted(word_list)
    graph_l_to_r = list()
    graph_r_to_l = list()
    for word in word_list:
        lr = l_to_r[word]
        rl = r_to_l[word]
        graph_l_to_r.append(lr)
        graph_r_to_l.append(rl)
        if len(sys.argv) < 3:
            print word, interval_dist(l_to_r[word]), lr, rl
        else:
            g.write(" ".join([str(word), str(interval_dist(l_to_r[word])), str(lr), str(rl), "\n"]))
    if len(sys.argv) > 2:
        g.close()

    print "Printing graph"
    plt.plot(graph_l_to_r, graph_r_to_l, 'ro')
    plt.axis([0,1,0,1])
    pp = PdfPages('graph.pdf')
    pp.savefig()
    pp.close()
