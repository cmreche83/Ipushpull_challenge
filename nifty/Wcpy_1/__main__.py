from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import uvicorn

from starlette.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
import json
import pandas
from sqlite3 import connect

dataset = pandas.read_csv("data/nifty50_all.csv")
all_symbols = dataset['Symbol'].drop_duplicates()
print(all_symbols.to_string())

#con = sqlite3.connect("tutorial.db")

async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol
    """
    symbol = request.path_params['symbol']
    
    #print(symbol)
    #print(request.url.path)
    #print(request.url)
    
    if dataset.loc[dataset['Symbol'] == symbol.upper()].size > 0:
        #VALID #json_symbol_prices_raw = dataset[["Date", "Open", "High", "Low", "Close"]].loc[dataset['Symbol'] == symbol.upper()].sort_values(by=['Date'], ascending=False).to_json(orient='records')
        #raw_json = json.loads(json_symbol_prices_raw)
        #json_symbol_prices = json.dumps(raw_json, indent=4).lower()
        #return JSONResponse(json_symbol_prices)
        
        df_symbols = dataset[["Date", "Open", "High", "Low", "Close"]]  # change order  of columns to match what was given as example in the JSON string
        df_symbol = df_symbols.loc[dataset['Symbol'] == symbol.upper()].sort_values(by=['Date'], ascending=False) # filter by symbol and reorder by ascending date
        
        opt_args = str(request.url).split(request.url.path)
        print(opt_args)
        if opt_args[1]!='':
            if "?year=" in opt_args[1]:
                #try:
                year_param = opt_args[1].split("?year=")[1]
                # NEED TO MOD HERE IN CASE YEAR NOT FOUND
                df_to_return = df_symbol[(df_symbol['Date']>=f'{year_param}-01-01') & (df_symbol['Date']<=f'{year_param}-12-31')]
                if len(df_to_return)>0:
                    json_to_return = df_to_return.to_json(orient='records')
                    price_response = JSONResponse(json_to_return)
                else:
                    #price_reponse = JSONResponse({'ERROR':'year provided not found or invalid'}, status_code=400, headers=None, media_type=None)
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Year provided not found or invalid",)
            else:
                # other arguments could be supported in the future if necessary here but for now will return 400
                # price_reponse = Response('ERROR : invalid argument', status_code=400, headers=None, media_type=None)
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid Argument",)
        else:
            # no extra filtering argument provided so need to return df_symbol in json format
            price_response = JSONResponse(df_symbol.to_json(orient='records'))
        
        #VALID #raw_json = json.loads(json_symbol_prices_raw)
        #json_symbol_prices = json.dumps(raw_json, indent=4).lower()
        #return JSONResponse(json_symbol_prices)
        # -------------------------------------------------------------
        return price_response
    else:
        price_reponse = JSONResponse({'ERROR':'Symbol provided not found or invalid'}, status_code=400, headers=None, media_type=None)
        return price_reponse
    # TODO:
    # 1) Return open, high, low & close prices for the requested symbol as json records
    # 2) Allow calling app to filter the data by year using an optional query parameter

    # Symbol data is stored in the file data/nifty50_all.csv

    # return JSONResponse({'implement': 'me'})

# URL routes
app = Starlette(debug=True, routes=[
    Route('/nifty/stocks/{symbol}', price_data),
    Route('/nifty/stocks/{symbol}', push_price_data)
])


def main() -> None:
    """
    start the server
    """
    uvicorn.run(app, host='0.0.0.0', port=8888)


# Entry point
if __name__ == "__main__":
    main()
