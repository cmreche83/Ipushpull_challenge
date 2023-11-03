from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import uvicorn

from starlette.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
import json
import pandas
import re


csv_file = "data/nifty50_all.csv"       # in order not to overwrite the original csv file, I use this global variable to switch to the new csv file once a post operation succeeded ( and make sure the get request use the new csv file subsequently )

def initialise_dataset():
    global csv_file
    print(csv_file)
    dataset = pandas.read_csv(csv_file)
    dataset['Symbol'] = dataset['Symbol'].str.upper()   # convert to upper case each symbol
    #all_symbols = dataset['Symbol'].drop_duplicates()
    #print(all_symbols.to_string())
    return dataset

#con = sqlite3.connect("tutorial.db")

async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol
    """
    symbol = request.path_params['symbol']
    
    # THIS FX INTENDS TO DO:
    # 1) Return open, high, low & close prices for the requested symbol as json records
    # 2) Allow calling app to filter the data by year using an optional query parameter

    # Symbol data is stored in the file data/nifty50_all.csv
    
    dataset = initialise_dataset()
    
    if dataset.loc[dataset['Symbol'] == symbol.upper()].size > 0:
        
        df_symbols = dataset[["Date", "Open", "High", "Low", "Close"]]  # change order  of columns to match what was given as example in the JSON string
        df_symbol = df_symbols.loc[dataset['Symbol'] == symbol.upper()].sort_values(by=['Date'], ascending=False) # filter by symbol and reorder by ascending date
        #df_symbol['Date'] = pandas.to_datetime(df_symbol['Date']).dt.strftime('%d/%m/%Y')
        
        opt_args = str(request.url).split(request.url.path) # -> ['http://localhost:8888', '?year=2017']
        if opt_args[1]!='':
            if "?year=" in opt_args[1]:
                #print("---------------- YEAR FILTER -----------------")
                year_param = opt_args[1].split("?year=")[1] # year_param should have now only the year value provided in the url
                if year_param.isnumeric:
                    #df_to_return = df_symbol[(df_symbol['Date']>=f'01/01/{year_param}') & (df_symbol['Date']<=f'31/12/{year_param}')] # try to filter the dataframe to only return rows for the specified year # interestingly this line of code does not work
                    df_to_return = df_symbol.loc[(df_symbol['Date']>=f'{year_param}-01-01') & (df_symbol['Date']<=f'{year_param}-12-31')] # try to filter the dataframe to only return rows for the specified year
                    df_to_return['Date'] = pandas.to_datetime(df_to_return['Date']).dt.strftime('%d/%m/%Y')
                    
                    json_to_return = df_to_return.to_json(orient='records') # converted to JSON
                    ## json_to_return = json.dumps(json_to_return, indent=4) # can be used to prettify the JSON string - commented out as, it would mean adding \n and indentations, so more characters so undesirable in real world scenario ( more chars to exchange over network -> lower performance )
                    price_response = JSONResponse(json.loads(json_to_return.lower())) # response to return
                else:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Year provided not found or invalid",)
            else:
                # other arguments could be supported in the future if necessary here but for now will return 400
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid Argument",)
        else:
            # no extra (year) filtering argument provided so need to return df_symbol in json format
            df_symbol['Date'] = pandas.to_datetime(df_symbol['Date']).dt.strftime('%d/%m/%Y')
            price_response = JSONResponse(json.loads(df_symbol.to_json(orient='records').lower()))
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Symbol provided not found or invalid",)
    return price_response
    

def valid_json_record(record:dict) -> dict:
    """valid_json_record(record:dict) -> dict
    returns {} if record provided is invalid - should be discarded
    returns a non empty dictionnary containing the partly reformatted record should the record be valid"""
    
    valid = False
    date_format = r'^\d{2}/\d{2}/\d{4}$'
    
    if len(list(record.keys())) > 5:
        print("Too many keys provided in the JSON posted !")
        return {}
    
    all_keys = {"Date":False, "Open":False, "High":False, "Low":False, "Close":False}
    cleaned_record = {}
    for k in record:    # goes through each key held by record
        if k.title() in all_keys.keys():
            if k.title() != "Date":
                if str(record[k]).replace(".", "").isnumeric():
                    cleaned_record[k.title()] = record[k]
                    all_keys[k.title()] = True
            else:
                if re.match(date_format, record[k]):
                    if int(record[k][0:2])<=31 and int(record[k][3:5])<=12:   # this extra condition checks if dd is not mm
                        cleaned_record[k.title()] = record[k]
                        all_keys[k.title()] = True
                    else:
                        # if dd and mm are inverted ... discard record
                        return {}
        else:
            # we have extra keys
            if str(record[k]).replace(".", "").isnumeric():
                return {} # the extra key holds a numeric value so - discard record ("no other price-types are acceptable")
            else:
                # the extra key does not hold a numeric value, hence this is not pricing info hence record could be valid
                # will not include this key value pair in the cleaned_record dict though
                continue
                
    for k in all_keys:
        if not all_keys[k]:
            #cleaned_record[k] = ""  
            # although we could have one pricing info missing from the record we want to insert, 
            # it would be discarded later on since, 
            # without one pricing info we cannot validate if it is within 1 std deviation or not 
            # so to save cpu, it will be discarded at this stage instead of later ( hence return {} )
            return {}
    
    if cleaned_record['Date'] != "":
        return cleaned_record
    else:
        return {}   # if no date provided I will discard the record as it cannot be determined if it would "update" existing data or "add" more data
        
def record_within_one_std_dev(clean_record:dict, symbol_df:pandas.core.frame.DataFrame, N=50):
    """record_within_one_std_dev(clean_record:dict, symbol_df:pandas.core.frame.DataFrame, N=50)
    returns True if pricing values are within one std_dev
    returns False if it is not the case """
    
    if N <= symbol_df.size:
        n = N
    else:   # in case I do have less than 50 values to compute the mean and std I will perform it with all the values I have instead of 50
        n = symbol_df.size
    
    _std = {}
    _mean = {}
    _range = {}
    pricings = ['Low', 'High', 'Open', 'Close']
    
    for k in pricings:
        _std[k] = symbol_df[k][0:n].std() # standard deviations
        _mean[k] = symbol_df[k][0:n].mean() # mean
        _range[k] = [_mean[k] - _std[k], _mean[k] + _std[k]] # 1std dev range
    
    print(_range)   # print statement for testing purposes - shows what are acceptable intervals within 1 std deviation
    
    valid = 0
    for k in _range:
        if (_range[k][0] < clean_record[k]) and (_range[k][1] > clean_record[k]):
            valid += 1
    if valid == 4:
        return True
    else:
        return False

async def push_price_data(request: Request) -> JSONResponse:
    # this function should cover all of question 3
    global csv_file
    symbol = request.path_params['symbol']
    
    dataset = initialise_dataset()
    symbol_df = dataset.loc[dataset['Symbol'] == symbol.upper()].sort_values(by=['Date'], ascending=False)  # filtered by symbol and sorted by date
    
    json_data = await request.json()    # at this stage, B can be a dictionnary (single record) or a list (multiple records)
    
    date_format = r'^\d{2}/\d{2}/\d{4}$'
    
    if type(json_data) is list:
        for record in json_data:
            # open, close, low, high must be present as keys ... date as well
            # date in DD/MM/YYYY 
            cleaned_record = valid_json_record(record)
            
            if cleaned_record != {}:
                date_for_dataset = f"{cleaned_record['Date'][-4:]}-{cleaned_record['Date'][3:5]}-{cleaned_record['Date'][0:2]}"
                
                ##if dataset.loc[dataset['Symbol'] == symbol.upper()].size > 0:
                if symbol_df.size > 0: # this symbol exist in our dataset
                    # verify is date is not already existing - add data, do not allow to change existing data/records
                    if symbol_df.loc[symbol_df['Date'] == date_for_dataset].size>0:  
                        #print("-----------------DATE EXISTS ----------------------------------")
                        #print(symbol_df.loc[symbol_df['Date'] == date_for_dataset])
                        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Blocked you from Overwritting data",)
                    else:
                        #print("-----------------STD DEVIATION AND INSERT----------------------")
                        if record_within_one_std_dev(cleaned_record, symbol_df):
                            # record validated will now be added to the dataset
                            cleaned_record['Symbol'] = symbol.upper()
                            dmy = cleaned_record['Date'].split("/")
                            cleaned_record['Date'] = f"{dmy[2]}-{dmy[1]}-{dmy[0]}"
                            dataset.loc[len(dataset)] = cleaned_record
                            dataset.to_csv('data/dataset.csv', index=False)
                            csv_file = 'data/dataset.csv'
                            print("new row inserted ...")
                        else:
                            print("discarded record because of std deviation")
                            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Data not within 1 std deviation so discarded",)
                else:   # this symbol is NOT in our dataset ( so I suppose will have to be added even if we won't be able to calc the std deviation since no data for it )
                    cleaned_record['Symbol'] = symbol.upper()       # add Symbol to record
                    dmy = cleaned_record['Date'].split("/")
                    cleaned_record['Date'] = f"{dmy[2]}-{dmy[1]}-{dmy[0]}"  # convert date format to match the one in csv
                    dataset.loc[len(dataset)] = cleaned_record
                    dataset.to_csv('data/dataset.csv', index=False)
                    csv_file = 'data/dataset.csv'
                    print("new symbol added ...")
    
    return JSONResponse({'status': 'New record added'})




def main() -> None:
    """
    start the server
    """
    # URL routes
    app = Starlette(debug=True, routes=[
        Route('/nifty/stocks/{symbol}', price_data, methods=['GET']),
        Route('/nifty/stocks/{symbol}', push_price_data, methods=['POST', 'PUT'])
    ])
    uvicorn.run(app, host='0.0.0.0', port=8888)

# Entry point
if __name__ == "__main__":
    main()
