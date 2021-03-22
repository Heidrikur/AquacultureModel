from flask import Flask, render_template, redirect, url_for, request, session, flash, g, make_response, send_file, send_from_directory, jsonify
from bokeh.plotting import output_notebook, figure
from bokeh.embed import components
from bokeh.models.sources import AjaxDataSource
from bokeh.models import LinearAxis, Range1d
from bokeh.resources import CDN
from math import exp,log
import environment as em
import plots as plotz

import numpy as np

app = Flask(__name__)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/')
def welcomepage():
    return render_template('welcome.html')

@app.route('/ref/')
def refpage():
    return render_template('ref.html')

@app.route('/add_data/')
def adddatapage():
    return render_template('add_data.html')

@app.route('/model/')
def show_page():
    Temp = 10
    Sal = 30
    VELO = 5
    SMR = 53.1
    EXP = 1.114
    Uopt = round(1/EXP,2)
    Ucrit = 1.8
    SDA = 41 # % of SMR
    CIRC = 160
    DEPT = 8
    NUMFISH = 150
    VOL = 16291
    FMASS = 2.5 # kg
    FLEN = 42 # cm
    O2envL = 8.44 #mg/l
    O2envm3 = O2envL*1000
    BLS = Uopt
    TMASS = round(FMASS*NUMFISH)
    FDEN = round((TMASS*1000)/VOL, 1)
    O2envL = round(em.beta1atm(Temp, Sal),2) # mg/L
    DIAM = round(CIRC/np.pi,1)
    RADI = round(DIAM/2, 1)
    RangePos = DIAM
    Sigmo10 = [327.5, 6.5, 3.5]
    Sigmo15 = [414.9, 6.04, 5.514]
    Sigmo20 = [388.1, 6.24, 5.7]
    SigmoList = [Sigmo10, Sigmo15, Sigmo20]
    SigmoSelect = myround(Temp)
    threshold = round(Threshold(Temp),1)
    thresholdval = round((threshold/100)*O2envL,1)
    script_MO2_U, div_MO2_U, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List = plotz.make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2envL, FLEN, DIAM,VELO, BLS, RangePos, SigmoList[SigmoSelect], threshold)
    
    Time2RestList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 0, threshold)
    Time2RestFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 1, threshold)
    Time2UoptList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 2, threshold)
    Time2UoptFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 3, threshold)

    MaxLengthList = MaxLengthCage(Con_size_List[0], Con_size_List[1], DIAM)
    MaxLengthListSDA = MaxLengthCage(Con_size_List[2], Con_size_List[3], DIAM)

    script1 = script_MO2_U
    div1 = div_MO2_U
    Study = 0

    cdn_js = CDN.js_files
    return render_template('index.html', SCRIPT=script_MO2_U, DIV=div_MO2_U, script1=script1, div1=div1,
        cdn_js=cdn_js[0], SMR=SMR, EXP=EXP, Ucrit=Ucrit, Uopt=Uopt, SDA=SDA, UoptFed=UoptFed, Temp=Temp, Sal=Sal,
        VELO=VELO, CIRC=CIRC, DEPT=DEPT, NUMFISH=NUMFISH, FMASS=FMASS, FLEN=FLEN, VOL=VOL, BLS=BLS, O2envL=O2envL,
        O2envm3=O2envm3, DIAM=DIAM, Study=Study, RADI=RADI, TMASS=TMASS, FDEN=FDEN, Time2RestList=Time2RestList, 
        Time2RestFedList=Time2RestFedList, Time2UoptList=Time2UoptList, Time2UoptFedList=Time2UoptFedList, 
        MaxLengthList=MaxLengthList, MaxLengthListSDA=MaxLengthListSDA)

def Threshold(Temperature): # From Remen 2020
    return 2.875*Temperature+22.85

#@app.route('/', methods=['POST'])
def MaxLengthCage(Inter, Slope, diameter):
    first = 1
    last = diameter
    center = last/2
    
    First = Slope*first+Inter
    Center = Slope*center+Inter
    Last = Slope*last+Inter
    
    onePercent = Inter/100
    FirstPer = First/onePercent
    CenterPer = Center/onePercent
    LastPer = Last/onePercent

    # Find at maximum range a cage can be
    SeventyLimit = ((Inter*0.7)-Inter)/Slope
    FourtyLimit = ((Inter*0.4)-Inter)/Slope
    ZeroLimit = ((Inter*0.0)-Inter)/Slope
    
    MaxLengthList = [round(First[0],1), round(Center[0],1), round(Last[0],1), round(FirstPer[0],1), round(CenterPer[0],1), round(LastPer[0],1), round(SeventyLimit[0],1), round(FourtyLimit[0],1), round(ZeroLimit[0],1)]
    return MaxLengthList

def Time2HypoFunc(InterList, SlopeList, i, Threshold):
    Threshold = Threshold/100
    T0 = ((InterList[i]*Threshold)-InterList[i])/SlopeList[i][0]
    T1 = ((InterList[i]*0.7)-InterList[i])/SlopeList[i][0]
    T2 = ((InterList[i]*0.4)-InterList[i])/SlopeList[i][0]
    T3 = ((InterList[i]*0.2)-InterList[i])/SlopeList[i][0]
    T4 = ((InterList[i]*0.0)-InterList[i])/SlopeList[i][0]
    T0 = '{0:02.0f}.{1:02.0f}'.format(*divmod(T0 * 60, 60))
    T1 = '{0:02.0f}.{1:02.0f}'.format(*divmod(T1 * 60, 60))
    T2 = '{0:02.0f}.{1:02.0f}'.format(*divmod(T2 * 60, 60))
    T3 = '{0:02.0f}.{1:02.0f}'.format(*divmod(T3 * 60, 60))
    T4 = '{0:02.0f}.{1:02.0f}'.format(*divmod(T4 * 60, 60))
    T0 = str(T0)+ " hours"
    T1 = str(T1)+ " hours"
    T2 = str(T2)+ " hours"
    T3 = str(T3)+ " hours"
    T4 = str(T4)+ " hours"

    #T0 = round(T0, 1)
    #T1 = round(T1, 1)
    #T2 = round(T2, 1)
    #T3 = round(T3, 1)
    #T4 = round(T4, 1)
    Time2RestList = [T1, T2, T3, T4, T0]
    
    return Time2RestList

def myround(x, base=5):
    target = base * round(x/base)
    if target <10:
        target = 10
    elif target > 20:
        target = 20

    if target == 10:
        target = 0
    elif target == 15:
        target = 1
    elif target == 20:
        target = 2
    return target

def MO2_U(x, a, b):
    return a * np.exp(b * x)

def calcCage(CIRC, Depth):
    Radius = round(CIRC/(2*np.pi),1)
    Diameter = round(CIRC/np.pi,1)
    Volume = round(np.pi*(CIRC/(2*np.pi))**2*Depth,1)
    return Diameter, Radius, Volume

def Database(indexDB):
    TempList = [10, 10, 15, 20, 20]
    #SMRList = [43.61, 53.1, 60.5, 104.1, 104.1]
    SMRList = [43.61, 53.08, 60.55, 104.06, 99.28]
    EXPList = [0.9987, 1.114, 0.909, 0.646, 0.646]
    #UcritList = [2.5, 1.8, 2.4, 2.4, 2.4]
    UcritList = [2.5, 2.4, 2.4, 2.4, 2.4]
    #LenList = [27.0, 51.1, 46.5, 44.6, 60.5]
    LenList = [27.0, 38.4, 38.4, 38.4, 60.5]
    #MassList = [0.2, 2.1, 1.4, 1.0, 4.5]
    MassList = [0.2, 1.4, 1.4, 1.4, 4.5]

    Temp = TempList[indexDB-1]
    SMR = SMRList[indexDB-1]
    EXP = EXPList[indexDB-1]
    Ucrit = UcritList[indexDB-1]
    FLEN = LenList[indexDB-1]
    FMASS = MassList[indexDB-1]
    Sal = 30
    return Temp, Sal, SMR, EXP, Ucrit, FLEN, FMASS

@app.route('/background_process')
def background_process():

    Study = request.args.get('inputStudy', 0, type=int)
    if Study != 0:
        Temp, Sal, SMR, EXP, Ucrit, FLEN, FMASS = Database(Study)
    else:
        Temp = request.args.get('inputTemp', 0, type=float)
        Sal = request.args.get('inputSal', 0, type=float)
        SMR = request.args.get('inputSMR', 0, type=float)
        EXP = request.args.get('inputEXP', 0, type=float)
        Ucrit = request.args.get('inputUcrit', 0, type=float)
        FLEN = request.args.get('inputFLEN', 0, type=float)
        FMASS = request.args.get('inputFMASS', 0, type=float) 
    
    O2envL = round(em.beta1atm(Temp, Sal),2) # mg/L
    O2envm3 = O2envL*1000
    SDA = request.args.get('inputSDA', 0, type=float)
    CIRC = request.args.get('inputCIRC', 0, type=float)
    DEPT = request.args.get('inputDEPT', 0, type=float)
    DIAM, RADI, VOL = calcCage(CIRC, DEPT)  
    VELO = request.args.get('inputVELO', 0, type=float)
    BLS = request.args.get('inputBLS', 0, type=float)
    NUMFISH = request.args.get('inputNUMFISH', 0, type=int)
    TMASS = (NUMFISH*1000)*FMASS
    FDEN = round(TMASS/VOL, 1)
    SS = round(BLS * FLEN,1)
    WF = round(VELO / FLEN, 1)
    RangePos = 1
    Sigmo10 = [327.5, 6.5, 3.5]
    Sigmo15 = [414.9, 6.04, 5.514]
    Sigmo20 = [388.1, 6.24, 5.7]
    SigmoList = [Sigmo10, Sigmo15, Sigmo20]
    SigmoSelect = myround(Temp)
    threshold = round(Threshold(Temp),1)
    thresholdval = round((threshold/100)*O2envL,1)
    SCRIPT, DIV, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List = plotz.make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2envL, FLEN, DIAM, VELO, BLS, RangePos, SigmoList[SigmoSelect],threshold)
    Time2RestList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 0, threshold)
    Time2RestFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 1, threshold)
    Time2UoptList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 2, threshold)
    Time2UoptFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 3, threshold)

    MaxLengthList = MaxLengthCage(Con_size_List[0], Con_size_List[1], DIAM)
    MaxLengthListSDA = MaxLengthCage(Con_size_List[2], Con_size_List[3], DIAM)
    
    UOPT = round(1/EXP,2)

    # Reset the study selector:
    Study = 0
    Sendback = {
                "O2envL" : O2envL,
                "O2envm3" : O2envm3,
                "UOPT" : UOPT,
                "UoptFed" : UoptFed,
                "SCRIPT" : SCRIPT,
                "DIV" : DIV,
                "VOL" : VOL,
                "DIAM" : DIAM,
                "RADI" : RADI,
                "TMASS" : TMASS,
                "Temp" : Temp,
                "SMR" : SMR,
                "EXP" : EXP,
                "Sal" : Sal,
                "Ucrit" : Ucrit,
                "FLEN" : FLEN,
                "FMASS" : FMASS,
                "FDEN" : FDEN,
                "SS" : SS,
                "WF" : WF,
                "Time2RestList": Time2RestList,
                "Time2RestFedList": Time2RestFedList,
                "Time2UoptList": Time2UoptList,
                "Time2UoptFedList": Time2UoptFedList,
                "MaxLengthList" : MaxLengthList,
                "MaxLengthListSDA" : MaxLengthListSDA,
                "threshold": threshold,
                "thresholdval":thresholdval
                }

    return jsonify(result = Sendback)

@app.route('/model/_Update_plots', methods=['GET','POST'])
def Update_plots():
    Study = request.form.get('inputStudy', type=int)
    if Study != 0:
        Temp, Sal, SMR, EXP, Ucrit, FLEN, FMASS = Database(Study)
    else:
        Temp = request.form.get('inputTemp', 0, type=float)
        Sal = request.form.get('inputSal', 0, type=float)
        SMR = request.form.get('inputSMR', 0, type=float)
        EXP = request.form.get('inputEXP', 0, type=float)
        Ucrit = request.form.get('inputUcrit', 0, type=float)
        FLEN = request.form.get('inputFLEN', 0, type=float)
        FMASS = request.form.get('inputFMASS', 0, type=float)
    
    #RangePos = request.form.get('inputRangePos', 1, type=int)
    O2envL = round(em.beta1atm(Temp, Sal),2) # mg/L
    SDA = request.form.get('inputSDA', 0, type=float)
    CIRC = request.form.get('inputCIRC', 0, type=float)
    DEPT = request.form.get('inputDEPT', 0, type=float)
    DIAM, RADI, VOL = calcCage(CIRC, DEPT)  
    RangePos = DIAM
    VELO = request.form.get('inputVELO', 0, type=float)
    BLS = request.form.get('inputBLS', 0, type=float)
    NUMFISH = request.form.get('inputNUMFISH', 0, type=int)
    TMASS = (NUMFISH*1000)*FMASS
    FDEN = round(TMASS/VOL, 1)
    Sigmo10 = [327.5, 6.5, 3.5]
    Sigmo15 = [414.9, 6.04, 5.514]
    Sigmo20 = [388.1, 6.24, 5.7]
    SigmoList = [Sigmo10, Sigmo15, Sigmo20]
    SigmoSelect = myround(Temp)
    threshold = round(Threshold(Temp),1)
    thresholdval = round((threshold/100)*O2envL,1)
    SCRIPT, DIV, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List = plotz.make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2envL, FLEN, DIAM, VELO, BLS, RangePos, SigmoList[SigmoSelect],threshold)
        
    return render_template('update_content.html', DIV=DIV, SCRIPT=SCRIPT, DIAM=DIAM)

if __name__ =="__main__":
    app.run(debug=True, port=8080, threaded=True)