# Home Bill Analysis

I created this analysis to understand why my home's PG&amp;E electric usage was so high.  This is a work in progress. Here's how you can use it:

1. Download your data from the GreenButton link on your PG&amp;E bill online.  Save the file to the `data` folder using the name given it by PG&amp;E.

2. Request weather data from NOAA LCD (https://www.ncdc.noaa.gov/cdo-web/datatools/lcd) for the months you downloaded from GreenButton.  Choose your zipcode or nearest airport and wait for the data to be delivered from NOAA.  Save the file to the `data` folder using the NOAA order number.

3. Edit the file `data/index.json` to add the `zipcode : weather` definition to "weather", and your `account : zipcode` definition to "accounts".

4. Run `main.py`.  The output will be a `.png` file with your account number.

