import os, config, json, datetime, pandas, pwlf, scipy, matplotlib.pyplot as plot

with open(f"{config.data}/index.json") as fh:
    index = json.load(fh)

def noaa_to_date(t):
    return datetime.datetime.fromisoformat(t)

def noaa_to_temperature(t):
    try:
        return float(t)
    except:
        if len(t) > 0:
            return noaa_to_temperature(t[0:-1])
        else:
            return float('nan')

for file in os.listdir(config.data):
    filespec = file.split('.')[0].split('_')
    if filespec[0:4] == ['pge','electric','interval','data'] and filespec[4] in config.account:
        usage = pandas.read_csv(f"{config.data}/{file}",
            header = 4,
            usecols = ['DATE','START TIME','END TIME','USAGE'],
            converters = {
                'USAGE' : float,
            }
            )
        usage['INDEX'] = usage[['DATE','START TIME']].apply(lambda dt: int(datetime.datetime.strptime(' '.join(dt),'%Y-%m-%d %H:%M').timestamp()/3600)-config.timezone,axis=1)
        usage['DT'] = ((usage[['DATE','END TIME']].apply(lambda dt: datetime.datetime.strptime(' '.join(dt),'%Y-%m-%d %H:%M').timestamp(),axis=1) - usage[['DATE','START TIME']].apply(lambda dt: datetime.datetime.strptime(' '.join(dt),'%Y-%m-%d %H:%M').timestamp(),axis=1))+60)/3600
        usage['USAGE'] = usage['USAGE'] / usage['DT']
        usage.set_index(keys='INDEX',inplace=True)
        usage.drop(columns=['DATE','START TIME','END TIME','DT'],inplace=True)
        usage.dropna(inplace=True)
        account = filespec[4]
        start = filespec[5]
        stop = filespec[7]
        location = index['accounts'][account]
        weather = pandas.read_csv(index['weather'][location],
            header = 0,
            usecols = ['DATE','HourlyDryBulbTemperature'],
            converters = {
                'DATE' : noaa_to_date,
                'HourlyDryBulbTemperature' : noaa_to_temperature
            }
            )
        weather.rename(columns={'HourlyDryBulbTemperature':'TEMPERATURE'},inplace=True)
        weather['INDEX'] = weather[['DATE']].apply(lambda dt: int(dt[0].timestamp()/3600),axis=1)
        weather.set_index('INDEX',inplace=True)

        data = weather.join(usage).dropna()
        data['HOUROFDAY'] = data.index % 24

        t = data['DATE']
        h = data['HOUROFDAY']
        T = data['TEMPERATURE']
        P = data['USAGE']

        fit = pwlf.PiecewiseLinFit(T,P)
        Tc = fit.fit(2)
        Sc = fit.calc_slopes()
        if Sc[0] > Sc[1]:
            Tc = [min(Tc),max(Tc)]
            Sc,i,r,p,s = scipy.stats.linregress(T,P)
        else:
            Sc = Sc[1]
            Tc = Tc[1:]
        print(f"Temperature sensitivity above {Tc[0]:.0f} degF: {Sc*1000:.0f} W/degF")

        fig, ax = plot.subplots(1,2,figsize=(13,5))

        ax[0].plot(T,P,'.')
        ax[0].grid()
        ax[0].set_xlabel('Outdoor temperature (degF)')
        ax[0].set_ylabel('Energy usage (kWh/h)')
        ax[0].plot(Tc,fit.predict(Tc),linewidth=2,color='black')

        ax[1].plot(h,P,'.')
        ax[1].grid()
        ax[1].set_xlabel('Hour of day')
        ax[1].set_ylabel('Energy usage (kWh/h)')
        ax[1].plot(range(24),data.set_index('HOUROFDAY').groupby('HOUROFDAY')['USAGE'].mean(),linewidth=2,color='black')

        fig.savefig(f"{account}.png");


