import random
def getopts(argv):
    opts = {}
    while argv:
        if argv[0][0] == '-':
            opts[argv[0]] = argv[1]
        argv = argv[1:]
    return opts

if __name__ == '__main__':
	from sys import argv
	myargs = getopts(argv)
	from time import sleep
	sleep(1)
	print {"i": myargs['--i'], "j": myargs['--j'], "k": myargs['--k'], "images": myargs['--images'], "accuracy": random.random()}