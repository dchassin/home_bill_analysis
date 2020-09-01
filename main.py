import os, config, json, datetime, pandas, pwlf, scipy, matplotlib.pyplot as plot

with open(f"{config.data}/index.json") as fh:
    index = json.load(fh)

tzdiff = round(datetime.datetime.utcnow().timestamp()-datetime.datetime.now().timestamp())/3600

def noaa_to_date(t):
    return datetime.datetime.strptime(t,"%Y-%m-%dT%H:%M:%S")

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
        usage['INDEX'] = usage[['DATE','START TIME']].apply(lambda dt: int(datetime.datetime.strptime(' '.join(dt),'%Y-%m-%d %H:%M').timestamp()/3600)-tzdiff,axis=1)
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
        data['DATE'] = data[['DATE']].apply(lambda dt: datetime.datetime(dt[0].year,dt[0].month,dt[0].day,dt[0].hour),axis=1)
        data.drop_duplicates(subset=['HOUROFDAY','TEMPERATURE','USAGE'],inplace=True)

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

        fig, ax = plot.subplots(2,2,figsize=(13,13))

        ax[0][0].plot(T,P,'.')
        ax[0][0].grid()
        ax[0][0].set_xlabel('Outdoor temperature (degF)')
        ax[0][0].set_ylabel('Energy usage (kWh/h)')
        ax[0][0].plot(Tc,fit.predict(Tc),linewidth=2,color='black',label=f"{Sc*1000:.0f} W/degF (>{Tc[0]:.0f} degF)")
        ax[0][0].legend();

        ax[0][1].plot(h,P,'.')
        ax[0][1].grid()
        ax[0][1].set_xlabel('Hour of day')
        ax[0][1].set_ylabel('Energy usage (kWh/h)')
        ax[0][1].plot(range(24),data.set_index('HOUROFDAY').groupby('HOUROFDAY')['USAGE'].mean(),linewidth=2,color='black')

        ax[1][0].plot(h,T,'.')
        ax[1][0].grid()
        ax[1][0].set_xlabel('Hour of day')
        ax[1][0].set_ylabel('Outdoor temperature (degF)')
        ax[1][0].plot(range(24),data.set_index('HOUROFDAY').groupby('HOUROFDAY')['TEMPERATURE'].mean(),linewidth=2,color='black')

        fig.savefig(f"{account}.png");

        data.to_csv(f"{account}.csv");


