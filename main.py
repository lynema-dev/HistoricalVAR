import pandas as pd
import numpy as np
import os
import math
import matplotlib.pylab as plt
from pandas.plotting import register_matplotlib_converters

def calculateVAR(valuationdate, percentile, binwidth):
    
    valuationdate = pd.to_datetime(valuationdate)

    curdirectory = str(os.path.dirname(os.path.realpath(__file__))) + '\\'
    cashflowfile = curdirectory + 'cashflows.csv'
    curvesfile = curdirectory + 'curves.csv'
    scenariosfile = curdirectory + 'scenarios.csv'

    if not os.path.exists(cashflowfile) or not os.path.exists(curvesfile) or not os.path.exists(scenariosfile):
        print ('Files not found!')
        return

    columns = ['pv']
    rows = []
    
    #process data files
    scenariosdf = pd.read_csv(scenariosfile)
    scenarios = scenariosdf.drop(['scenariodate'],axis = 1).to_numpy()

    curvesdf = pd.read_csv(curvesfile)
    curvesdf['tenor'] = curvesdf['tenor'].str.replace('y','')
    curvesdf['tenor'] = pd.to_numeric(curvesdf['tenor'])
    tenors = curvesdf['tenor'].transpose().to_numpy()

    curvedf = curvesdf.drop(['indexname','tenor'],axis = 1)
    curve = curvedf.transpose().to_numpy().flatten()

    cashflowsdf = pd.read_csv(cashflowfile)
    cashflowsdf['yearfrac'] = (pd.to_datetime(cashflowsdf['paydate']) - valuationdate) /np.timedelta64(1,'Y')

    #baseline pv of cashflow series
    flatpv = 0
    for row in cashflowsdf.iterrows():
        yearfrac = float(row[1].yearfrac)
        cashflow = float(row[1].amount)
        rate = np.interp(yearfrac, tenors, curve)
        df = 1 / ((1 + rate / 100) ** yearfrac)
        flatpv += (cashflow * df)

    #create bumped curves and pv the cashflows
    print ('calculating results from ' + str(len(scenarios)) + ' scenarios ...')
    for i in range(len(scenarios)):
        pv = 0
        scenario = scenarios[(i),0:]
        bumpedrates = curve + scenario

        for row in cashflowsdf.iterrows():
            yearfrac = float(row[1].yearfrac)
            cashflow = float(row[1].amount)
            bumpedrate = np.interp(yearfrac, tenors, bumpedrates)
            df = 1 / ((1 + bumpedrate / 100) ** yearfrac)
            pv += (cashflow * df)

        row = [round(pv-flatpv,0)]
        rows.append(row)

    dfoutput = pd.DataFrame(rows, columns = columns)
    outputarray = dfoutput.to_numpy()

    var = round(np.percentile(outputarray,percentile * 100),0)
    printstring = 'pv = ' + format(round(flatpv,0),',.0f') + ', 1 month ' + str(100 - (percentile * 100)) 
    printstring += ', % var = ' + format(var,',.0f') + ', n=' +  format(len(scenarios),'')

    print (printstring)

    min = outputarray.min()
    max = outputarray.max()

    roundfactor = math.log(binwidth) / math.log(10)
    roundfactor = int(roundfactor)

    minrange = round(min - 2* binwidth,-roundfactor)
    maxrange = round(max + 2 * binwidth, -roundfactor)
    numberofbins = (maxrange - minrange) / binwidth

    hg = np.histogram(outputarray, int(numberofbins), (minrange , maxrange))
    bin_edges = hg[1]
    hist = hg[0]

    for i in range(len(bin_edges)):
        if bin_edges[i] > var:
            plotpoint = i
            break

    register_matplotlib_converters()

    plt.bar(bin_edges[:-1], hist, width = binwidth, color = 'lightslategrey', edgecolor = 'slategrey')
    plt.bar(bin_edges[0:plotpoint], hist[0:plotpoint], width = binwidth, color = 'red', edgecolor = 'firebrick')
    plt.title(printstring)
    plt.show()


if __name__ == '__main__':

    valuationdate = '30/04/2020'
    percentile = 0.05
    binwidth = 100000

    calculateVAR(valuationdate, percentile, binwidth)



