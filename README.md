# pylontech-victron-bms-canbus-reader

## USE AT YOUR OWN RISK

This has only been used in combination with Pylontech US2000C and Victron Cerbox GX and a 
Raspberry PI connected to the CAN bus between Victron & Pylontech battery. 

⚠️ Implementation largely based on [scarce unofficial or outdated documentation / information](research/) found online

⚠️ Correctness of reading of warning and alarm canbus messages has not been really tested. DO NOT USE IT FOR CRITICAL SAFETY PURPOSES 


## Samples

### Print battery status
```shell
python3 main.py -i can0 -v
```


### Process candump file
```shell
python3 main.py -l candump.log -vv
```