import requests
import json

def test1():
    x = requests.get('http://localhost:8888/nifty/stocks/tatamotors')
    
    must_contain = '{"date":"26/12/2003","open":435.8,"high":440.5,"low":431.65,"close":430.95}'
    
    if must_contain in x.text:
        print("test1 passed")
        return True
    else:
        print("test1 failed")
        return False

def test2():
    # checks if filtering the year (question 2) works of not
    x = requests.get('http://localhost:8888/nifty/stocks/tatamotors?year=2017')
    records = x.text.replace("}","}\n")
    records = records.split("\n")
    for line in records:
        if "{" in line:         # the last line will not necessarily contain a record that's why this condition to exclude it
            if line[16:20] != '2017':
                print("test2 failed")
                return False
        else:
            continue
    print("test2 passed")
    return True
    
def test3():
    # test if error 400 when passing something wrong in the url param
    x = requests.get('http://localhost:8888/nifty/stocks/tatamotors/?yr=2017')
    if x.status_code == 400:
        print("test3 passed")
        return True
    else:
        print("test3 failed")
        return False

def test4():
    x = requests.get('http://localhost:8888/nifty/stocks/tatamotors/?year=2035')
    if x.text == "[]":
        print("test4 passed")
        return True
    else:
        print("test4 failed")
        return False
    
#def test5():
#    requests.post('http://localhost:8888/nifty/stocks/tatamotors', data='[{"open":32.0, "close":31.1, "low":10.0, "high":40.0, "date":"01/06/2021"}, {"open":32.0, "close":31.1, "low":10.0, "high":40.0}]')
#    # should not add anything since not within standard deviation or no date provided so invalid record

#def test6():
#    requests.post('http://localhost:8888/nifty/stocks/tatamotors', data='[{"open":300.0, "close":320.1, "low":295.0, "high":330.0, "date":"01/06/2021"}]')
#    # should add one record to tatamotors
    
#def test7():
#    requests.post('http://localhost:8888/nifty/stocks/abcdefg', data='[{"open":300.1, "close":320.0, "low":295.1, "high":330.1, "date":"02/06/2021"}]')
#    # should add a record and create the symbol abcdefg
    
if __name__ == "__main__":
    print("please run this script after running the application on another process")
    
    test1()
    test2()
    test3()
    test4()