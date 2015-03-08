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
        if (not reverse and (s * 100 + currentPosition > maxLength)) or (reverse and (s * 100 + currentPosition < maxLength)):
            # Link this row to the next row and reverse the direction
            if reverse:
                print "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition - interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition -= interludeSize/2
            else:
                print "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition += interludeSize/2
            yAdjustment += ySeparation
            reverse = not reverse
        if not reverse:
            print "translate([%f, %f, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition, cubeSize, s * 100, cubeSize)
            print "translate([%f, %f, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + (s * 100), interludeSize, separation, interludeSize)
        else:
            print "translate([%f, %f, %f]) rotate([180, 0 ,0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition, cubeSize, cubeSize, s * 100, cubeSize)
            print "translate([%f, %f, %f]) rotate([180, 0, 0]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition - (s * 100), cubeSize, interludeSize, separation, interludeSize)
        if reverse:
            currentPosition -= (s * 100) + separation
        else:
            currentPosition += (s * 100) + separation

if __name__ == "__main__":
    phrase = "List of US Presidents"
    enc = ArithmeticEncoder("arithmetic/English_word_list.txt")
    sequence = enc.encodePhrase(phrase)
    createConnections(sequence, 5)
    # print sequence
    # print enc.decodeSet(sequence)
