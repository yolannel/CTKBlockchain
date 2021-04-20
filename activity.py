import random
import os


def run(a):
    i = random.randint(1, 8)
    for x in range(0, int(a)):
        i = random.randint(1, 9)
        if i <= 3:
            firstTrans()
        elif 3 < i <= 6:
            secTrans()
        elif i == 7:
            firstMine()
        else:
            secMine()


def firstTrans():
    amount = random.randint(1, 50)
    s = "curl -X POST -H \"Content-Type: application/json\" -d \"{\\\"sender\\\": \\\"me\\\", "
    s1 = "\\\"recipient\\\": \\\"someone-other-address\\\", \\\"amount\\\": " + str(amount)
    s2 = "}\" http://127.0.0.1:5000/transactions/new"
    final = s+s1+s2
    os.system(final)


def secTrans():
    amount = random.randint(1, 50)
    s = "curl -X POST -H \"Content-Type: application/json\" -d \"{\\\"sender\\\": \\\"me\\\", "
    s1 = "\\\"recipient\\\": \\\"someone-other-address\\\", \\\"amount\\\": " + str(amount)
    s2 = "}\" http://127.0.0.1:5001/transactions/new"
    final = s + s1 + s2
    os.system(final)


def firstMine():
    os.system("curl -X GET http://127.0.0.1:5000/mine")


def secMine():
    os.system("curl -X GET http://127.0.0.1:5001/mine")
