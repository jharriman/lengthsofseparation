from arithmetic.compression import ArithmeticEncoder

def createConnections(sequence, maxLength):
    # Settings
    separation = 4
    cubeSize = 3
    interludeSize = 1
    ySeparation = 4
    scale = 50

    # Counters
    currentPosition = 0.0
    yAdjustment = 0.0
    reverse = False

    # Output string
    output = ""

    # Since we don't want to print an interlude if it's the last one, we initialize with a blank
    interlude=""

    # Expecting a sequence of tuples that specify the direction that the
    # length will be applied to
    for seq in sequence:
        output += interlude
        # Allow for overshooting past the maxlength, but only for one value
        if (not reverse and (currentPosition > maxLength)) or (reverse and (currentPosition < -maxLength)):
            # Link this row to the next row
            if reverse:
                output += "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition -= interludeSize/2
            else:
                output += "translate([%f, %f, 0]) rotate([0,0,-90]) cube([%f, %f, %f]);" % (yAdjustment, currentPosition + interludeSize/2, interludeSize, separation, interludeSize)
                currentPosition += interludeSize/2
            # Reverse the direction
            yAdjustment += ySeparation
            reverse = not reverse

        # Remove vertical/horizontal dependency
        s = seq[1]

        # Determine length direction
        yFlip = (0 if not seq[0] else 180) if reverse else 0
        xyz = (cubeSize, s * scale, cubeSize) if not seq[0] else (cubeSize, cubeSize, s * scale)
        horizontalLength = s * scale if not seq[0] else cubeSize
        towerYAdjustment = 0 if not seq[0] else cubeSize
        zAdjustment = cubeSize if not seq[0] else 0

        # Print out depending on our direction
        if not reverse:
            # Segment output
            segmentArgs = (yAdjustment, currentPosition, yFlip) + xyz
            output += "translate([%f, %f, 0]) rotate([0,%f,0]) cube([%f, %f, %f]);" % segmentArgs

            # Interlude output
            interludeArgs = (yAdjustment, currentPosition + horizontalLength, interludeSize, separation, interludeSize)
            interlude = "translate([%f, %f, 0]) rotate([0,0,0]) cube([%f, %f, %f]);" % interludeArgs

            # Update position
            currentPosition += horizontalLength + separation
        else:
            # Segment
            segmentArgs = (yAdjustment + towerYAdjustment, currentPosition, zAdjustment, yFlip) + xyz
            output += "translate([%f, %f, %f]) rotate([180, %f ,0]) cube([%f, %f, %f]);" % segmentArgs

            # Interlude
            interludeArgs = (yAdjustment, currentPosition - horizontalLength, interludeSize, interludeSize, separation, interludeSize)
            interlude += "translate([%f, %f, %f]) rotate([180, 0, 0]) cube([%f, %f, %f]);" % interludeArgs

            # Update position
            currentPosition -= horizontalLength + separation

    return output

# Testing output
if __name__ == "__main__":
    phrase = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.".replace(".", "").replace(",", "")
    enc = ArithmeticEncoder("data/words/English_word_list.txt")
    sequence = enc.encodePhrase(phrase)
    import random
    sequence = zip([random.choice([0,1]) for _ in sequence], sequence)
    print createConnections(sequence, 10)
