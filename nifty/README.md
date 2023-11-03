# Notes regarding this program


## Different approaches
When reading carefully the task description, I thought of different possible approaches to achieve the same goal :
- Using only the CSV file and do all the data processing / sorting and filtering using Python only
- Converting and importing/loading the CSV file provided in a SQL database and make the database do most of the work
- Another way this could be coded as well is by trying to minimise the amount of external libraries being used ( I won't go with this approach this time as typically, in the context of a programming tests, some people evaluating it could see it as a form of lack of knowledge of the programming language libraries - while the advantage of doing so is to have a program which maintenance is far less dependent on what the latest updates brought to the libraries/dependencies )
This is however an exercise and so it aims at testing the developper capabilities and that's something I try to keep in mind.

In a real world scenario, my preference would be the second option as it would allow to share the CPU load between the computer running Python ( taking care of handling the network aspect and refining result from SQL queries if needed ) and the SQL database server.
In the "Additional Information" section of the task description : "You may use any appropriate open source libs as part of your solution". Although SQL Lite is installed by default when installing Python. It is a library but relies on a Light SQL server software (even if that one is bundled with Python). Hence this could be considered both a right or a wrong approach depending on how that sentence is interpreted.

## Assumptions
I am sure I will forget a few in this section but at least the most notable ones are mentionned.

Regarding the standard deviation : 
- I made the assumption that if I have less than 50 records for a symbol, I would still check if the new record I am trying to add is within 1 std deviation ( using all the records for that std deviation )

Regarding adding data and not updating / overwritting existing records:
- I made the assumption that if a symbol does not exists, I should be able to create a new one ( even if it means I cannot check if the pricing info would be within 1 std deviation )
- I made the assumption that even if a record I try to add has only one pricing info missing, since the standard deviation cannot be verified, it should not be added to the dataset

## Real world scenario differences
- As a coding task it is ok to leave only functional programming code, since there is not a lot of code I left it this way. I would however make sure to have everything in a class instead for a real solution.
- This app is not secure so it would have to be revisited with that in mind : 
        * use of https instead of http ? This means making sure the SSL certificate associated never expires
        * Further encryption and eventually compression ?
- Use a database (SQL or NoSQL) : besides performance improvement, it could also improve performance, reliability and scalability
- (optional) Virtualization / Containerization : should we need to scale the python application depending on the load we could expect
- review the standard deviation aspect : the standard deviation calculation assumes what we have follow a distribution with a bell shaped curve. In practice, the bell shaped curved is often not symetrical. Assessing this lack of symetry could be something to look into / double check to make sure we do not discard valid records.

## ERRATA
the example provided for GET /nifty/stocks/tatamotors/
is a bit wrong : close price for tatamotors on the "26/12/2003" is 430.95 in the csv file provided instead of 438.6

Date,Symbol,Close,Open,High,Low
2003-12-26,TATAMOTORS,430.95,435.8,440.5,431.65