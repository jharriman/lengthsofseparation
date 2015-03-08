from arithmetic.compression import ArithmeticEncoder

def createConnections(sequence, maxLength):
    # Settings
    separation = 1.5
    cubeSize = 1
    interludeSize = 0.5
    ySeparation = 1.5

    # Counters
    currentPosition = 0.0
    yAdjustment = 0.0
    reverse = False

    for s in sequence:
        # Allow for overshooting past the maxlength, but only for one value
        if (not reverse and (currentPosition > maxLength)) or (reverse and (currentPosition < maxLength)):
            # Link this row to the next row
            if reverse:
                print "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition -= interludeSize/2
            else:
                print "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition += interludeSize/2
            # Reverse the direction
            yAdjustment += ySeparation
            reverse = not reverse
        if not reverse:
            print "translate([%f, %f, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition, cubeSize, s * 100, cubeSize)
            print "translate([%f, %f, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + (s * 100), interludeSize, separation, interludeSize)
            currentPosition += (s * 100) + separation
        else:
            print "translate([%f, %f, %f]) rotate([180, 0 ,0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition, cubeSize, cubeSize, s * 100, cubeSize)
            print "translate([%f, %f, %f]) rotate([180, 0, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition - (s * 100), interludeSize, interludeSize, separation, interludeSize)
            currentPosition -= (s * 100) + separation

if __name__ == "__main__":
    phrase = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.".replace(".", "").replace(",", "")
    enc = ArithmeticEncoder("arithmetic/English_word_list.txt")
    sequence = enc.encodePhrase(phrase)
    createConnections(sequence, 5)
    # print sequence
    # print enc.decodeSet(sequence)
