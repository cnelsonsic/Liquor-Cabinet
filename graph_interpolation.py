#!/usr/bin/env python

#Given two sets of data, x being time, y being amount of booze available:
data = ((0, 100), (1, 80), (2, 50), (4, 30), (6, 20))

#Solve for any higher x:
x = []
y = []
for d in data:
    x.append(d[0])
    y.append(d[1])

def yIntercept(x_1, y_1, x_2, y_2):
    '''From: Daniel Yoo <http://mail.python.org/pipermail/tutor/2000-August/002065.html>'''
    x_1, y_1, x_2, y_2 = map(float, [x_1, y_1, x_2, y_2])    # tricky!
    return y_1 - (y_2 - y_1)/(x_2 - x_1) * x_1
    
def extrapolate_to_y_zero_linear(x, y):
    '''Think this function's name is long enough?'''
    zerox = yIntercept(y[0], x[0], y[-1], x[-1])
    gx = x+[zerox]
    gy = y+[0]
    return gx, gy
    
def extrapolate_to_y_zero(x, y):
    from scipy.interpolate import UnivariateSpline
    '''Extrapolates a given set of data to find where y<=0.
    Requires scipy to work, may provide better/more interesting results 
    than the simple linear version.'''
    origy = y
    wantedx = x+[]
    tryagain = True
    origwantedxlen = len(wantedx)
    k = 3
    while tryagain:
        wantedx.append(wantedx[-1]+0.25)
        extrapolator = UnivariateSpline(x, origy, k=k, s=len(wantedx))
        y = extrapolator(wantedx)
        for i in y:
            if i < 0:
                tryagain = False
                #print origwantedxlen
                wantedx = wantedx[:origwantedxlen]+[wantedx[-1]]
                #print wantedx
                y = extrapolator(wantedx)
                break
                
        if len(wantedx) > len(x)*100:
            k -= 1
            #print "Hopeless. Lowering K value..."
            if k < 1: 
                tryagain = False
            
    return wantedx, y



