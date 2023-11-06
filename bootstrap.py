#!/usr/bin/env python3
# Blaest Bootstrap, or Blaeststrap if you will
# This is a simple python transpiler that transpiles Blaest into C, this is to
# enable the next generation Blaest compiler to be written in Blaest itself
# This may also help illustrate how a compiler/transpiler works, so care has 
# been taken to make this code as readable as possible

import sys

if len(sys.argv) != 2:
    print("USAGE: bootstrap.py [FILE.B]\n")
    print("Output file will be named whatever the given file is named, with .c")
    print("appended to the end. Ex: file.b -> file.b.c\n")
    print("Make sure the directory you compile the resulting c file in has")
    print("The library 'bglue.c' in the same folder")
    exit(1)

fname = sys.argv[1]

# The file we will read from and write to
file = open(fname, "r")
out = open(fname + ".c", "w")

# A registry of our variable we define
# TODO: this does not account for scopes, like blocks. This is just every 
# variable ever defined. Eventually this should clear when we leave a scope
# where the variable was defined 
VARIABLES = []

# Gets a single character from a file
def getChar():
    return file.read(1)

# Writes our transpiled output
def tpileWrite(oput):
    out.write(oput)

# Loop to parse a string
# - buffer: The buffer containing the string we are making sense of
def parseString(buffer):
    stringBuffer = ""
    ret = 0
    for i in range(0, len(buffer)):
        c = buffer[i]

        if c == '\"':
            # C transpiler output
            tpileWrite("(bword_t)\"" + stringBuffer + "\"")
            return i

        stringBuffer += c
    
    
    print("Error: Unclosed string!")
    exit(1)

# Loop to parse a function with arguments
# - buffer: the buffer that contains the arguments
def parseFunctionArgs(buffer):
    argBuffer = ""

    for c in buffer:

        if c == ')':
            parseValue(argBuffer)
            tpileWrite(")")
            return
        elif c == ',':
            parseValue(argBuffer)
            tpileWrite(", ")
            argBuffer = ""
        else:
            argBuffer += c

    
    print("Error: Unclosed function")
    exit(1)

# Loop to parse a function argument defintion
# - buffer: The buffer with our definition
def parseFunctionArgsDefn(buffer):
    argBuffer = ""

    for c in buffer:

        if c == ')':
            tpileWrite("bword_t " + argBuffer)
            tpileWrite(")")
            return
        elif c == ',':
            tpileWrite("bword_t " + argBuffer)
            tpileWrite(", ")
            argBuffer = ""
        else:
            argBuffer += c

    
    print("Error: Unclosed function")
    exit(1)

# Parse a value. This could be something like '5' or as broad as 'x = 5'. As 
# long as it returns something. Note that this function truncates spaces unless
# a string is found.
# - buffer: the buffer containing the value
def parseValue(buffer):
    global VARIABLES

    valueBuffer = ""
    i = 0

    while i < len(buffer):
        c = buffer[i]

        if not c:
            print("Encountered EOF while parsing statement")
            exit(1)
        
        if c == '\"':
            i += parseString(buffer[i + 1:])
            return
        elif c == '=':
            # We have a value assign statement

            # Make sure the variable is real
            if not valueBuffer in VARIABLES:
                print("Variable " + valueBuffer + " does not exist!")
                exit(1)
            
            tpileWrite(valueBuffer + " = ")
            valueBuffer = ""

            # Now the rest of this should be another value statement
            parseValue(buffer[i + 1:])
            return
        elif c == '(' and valueBuffer[-1].isalpha():
            # We have a function call
            tpileWrite("B_" + valueBuffer + "(")
            parseFunctionArgs(buffer[i + 1:])
            return

        elif c > ' ':
            valueBuffer += c

        i += 1

    # If we get here, its either a math statement or a variable 
    # We should probably error if its wrong, but lets let C handle that for now

    if valueBuffer.isalpha() and not valueBuffer in VARIABLES:
        print("ERROR: Variable " + valueBuffer + " not found!")
        exit(1)

    # C Transpiler output:
    tpileWrite(valueBuffer)

# Parse an auto statement. This is a keyword to define a varaible.
def parseAuto():
    global VARIABLES
    nameBuffer = ""

    while True:
        c = getChar()

        if not c:
            print("Encountered EOF while parsing statement")
            exit(1)

        # TODO: Make sure the variable we are defining has not previously been
        # defined in this scope

        #TODO: Add support for initializing arrays, such as 'auto x[5]'
        if c == ',':
            # Got a line like "auto x, y;"

            # C transpiler output:
            tpileWrite("bword_t " + nameBuffer + ";\n")
            VARIABLES.append(nameBuffer)
            
            nameBuffer = ""
        elif c == '=':
            # Got a line like "auto x = 5"
            
            # C transpiler output:
            tpileWrite("bword_t " + nameBuffer + " = ")
            VARIABLES.append(nameBuffer)

            nameBuffer = ""
            valueBuffer = ""

            while c != ';':
                c = getChar()

                if not c:
                    print ("EOF")
                    exit(1)
                
                valueBuffer += c
            
            parseValue(valueBuffer)

            # C transpiler output:
            tpileWrite(";\n")

            break
        elif c == ';':
            tpileWrite("bword_t " + nameBuffer + ";\n")
            VARIABLES.append(nameBuffer)
            break
        elif c > ' ':
            nameBuffer += c

# Parse a block of code, that is code that is between { and }
def parseBlock():
    
    lineBuffer = ""

    # C transpiler output
    tpileWrite("{\n")

    while True:
        c = getChar()

        if not c:
            print("Encountered EOF while parsing block")
            return
        
        # Exit the loop if we find }
        if c == '}':

            # C transpiler output
            tpileWrite("}\n")

            break

        # We got a block in our block 
        elif c == '{':
            parseBlock()

        # We have a line that didnt start with any keywords
        elif c == ';':
            parseValue(lineBuffer)
            tpileWrite(";\n")
            lineBuffer = ""
            
        else:
            lineBuffer += c

            # Look for patterns in the lineBuffer
            if lineBuffer.lstrip() == "auto":
                parseAuto()
                lineBuffer = ""
            elif lineBuffer.lstrip() == "return":
                c = getChar()
                tpileWrite("return ")

                lineBuffer = ""
                while c != ';':
                    lineBuffer += c
                    c = getChar()
                
                # Parse the return value
                parseValue(lineBuffer)

                lineBuffer = ""

                tpileWrite(";\n")


# Parse our global scope. This is code that is not in any function.
# This is the entrypoint to the transpiler
def parseGlobalScope():
    global VARIABLES
    globalBuffer = ""

    tpileWrite("#include \"bglue.c\"\n")

    while True:
        c = getChar()

        if not c:
            return
        
        # We have a function definition
        if c == '(':
            tpileWrite("bword_t B_" + globalBuffer + "(")
            VARIABLES.append(globalBuffer)

            globalBuffer = ""

            while c != ')':
                c = getChar()
                
                if not c:
                    print("ERROR: EOF while reading function definiton")
                    exit(1)
                else:
                    globalBuffer += c
            
            parseFunctionArgsDefn(globalBuffer)

            while c != '{':
                c = getChar()
                
                if not c:
                    print("ERROR: EOF while looking for function block")
                    exit(1)
            
            parseBlock()
            globalBuffer = ""

        # We have a global variable definiton
        elif c == '=':
            tpileWrite("bword_t " + globalBuffer + " = ")
            VARIABLES.append(globalBuffer)
            
            globalBuffer = ""

            c = getChar()
            while c != ';':

                if not c:
                    print("ERROR: EOF while looking for global variable value")
                    exit(1)
                else:
                    globalBuffer += c 

                c = getChar()
            
            parseValue(globalBuffer)

            tpileWrite(";\n")

            globalBuffer = ""
        elif c > ' ':
            globalBuffer += c 

# Start the transpilation
parseGlobalScope()