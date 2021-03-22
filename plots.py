import numpy as np
from bokeh.plotting import output_notebook, ColumnDataSource, figure, output_file, show
from bokeh.layouts import row, column
from bokeh.embed import components, file_html
from bokeh.models import Band, Title, CustomJS, Slider, LinearAxis, Range1d, Span
from bokeh.models.tools import CustomJSHover
from scipy.optimize import curve_fit
from bokeh.palettes import Turbo256
from sklearn.linear_model import LinearRegression
#from matplotlib.colors import LinearSegmentedColormap



def MO2_U(x, a, b):
    return a * np.exp(b * x)

def Rev_MO2_U(y, a, b):
    return np.log(y/a)/b

def SigmaSoid(x, Vm, b, c): # The Hill equation
    return Vm / (1 + ((b/x)**c))

def Time2Hypo(MO2, O2refvol, f_dens):
    MO2_s=MO2/3600 # MO2 pr second
    O2refvol = O2refvol*1000
    # Timescale array goes from 0 to 5*1H by increments of 1000.
    #TimeScale = np.array(np.linspace(0,100*3600,1000)).reshape((-1,1))
    TimeScale = np.array(np.arange(0,10*3600,1)).reshape((-1,1))
    TimeScaleList = []
    for i in TimeScale:
        TimeScaleList.append(i[0])
    # Create a list to contain the decrease in oxygen
    O2envListMO2 = []
    #O2envList10Uopt = []
    O2Concentration = O2refvol
    for c in TimeScaleList:
        O2Consump = (MO2_s*f_dens)*1
        O2Concentration = O2Concentration-O2Consump
        O2envListMO2.append(O2Concentration)
    O2envListMO2 = [ele for ele in O2envListMO2 if ele > 0]
    TimeScaleList = TimeScaleList[:len(O2envListMO2)]

    return TimeScaleList, O2envListMO2


def Time2HypoAdv(MO2, O2refvol, f_dens, SigmoList, SMR, EXP):
    MO2_s=MO2/3600 # MO2 pr second
    O2refvol = O2refvol*1000
    # Timescale array goes from 0 to 5*1H by increments of 1000.
    #TimeScale = np.array(np.linspace(0,10*3600,1000)).reshape((-1,1))
    TimeScale = np.array(np.arange(0,10*3600,1)).reshape((-1,1))
    TimeScaleList = []
    for i in TimeScale:
        TimeScaleList.append(i[0])

    # Create a list to contain the decrease in oxygen
    O2envListMO2 = []
    UnfedO2Cons = O2refvol
    for c in TimeScaleList:
        # Calculate a consumption
        O2Con = (MO2_s*f_dens)*1 # Oxygen consumption for all fish for each second
        UnfedO2ConsTester = UnfedO2Cons-O2Con

        pO2Calc = (20.94/(O2refvol))*UnfedO2ConsTester
        MaxMO2 = SigmaSoid(pO2Calc, *SigmoList)
        if MO2_s*3600 >= MaxMO2: # If the scope is lower than the used oxygen, find a new swimming speed           
            MO2_s = MaxMO2/3600
            if MO2_s <= SMR/3600:
                MO2_s = SMR/3600
            O2Con = (MO2_s*f_dens)*1 # Oxygen consumption for all fish for each second
            UnfedO2Cons = UnfedO2Cons-O2Con
        else:
            UnfedO2Cons = UnfedO2Cons-O2Con
        if UnfedO2Cons <= 0:
            break
        O2envListMO2.append(UnfedO2Cons)
    TimeScaleList = TimeScaleList[:len(O2envListMO2)]
    O2envListMO2 = [ele for ele in O2envListMO2 if ele > 0]
    
    #UnfedO2Con = O2refvol*1000
    #pO2Calc = (20.94/(O2refvol*1000))*UnfedO2Con
    


    return TimeScaleList, O2envListMO2

def regMaxCage(x,y):
        x = x.reshape((-1, 1))
        model = LinearRegression()
        model.fit(x, y)
        model = LinearRegression().fit(x, y)
        intercept = model.intercept_
        slope = model.coef_
        return intercept, slope

############################################################ Swimming energetics: MO2_U and COT + SDA ################################################################
def Plot_1_calc(SMR, EXP, Ucrit, SDA):
    # Calculate the magnitude of SDA
    SDA_Calc = SMR*(SDA/100)
    
    # Generate lists
    y = []
    x = np.linspace(0,Ucrit,500)
    y_COT = []
    x_COT = []
    x_SDA = []
    y_SDA = []
    x_COT_SDA = []
    y_COT_SDA = []

    # Create plot data for none fed fish    
    for i in x:
        y.append(MO2_U(i, SMR, EXP))
        if i > 0.1:
            y_COT.append(MO2_U(i, SMR, EXP)/i)
            x_COT.append(i)

    for i in y:
        y_SDA.append(i+SDA_Calc)

    position = np.argmax(y_SDA > y[-1])
    x_SDA = x[:position]
    y_SDA = y_SDA[:position]

    if SDA != 0:
        # find the fit for the SDA exponential function
        popt_SDA, _ = curve_fit(MO2_U, x_SDA, y_SDA)
        
        for i in x_SDA:
            if i > 0:
                x_COT_SDA.append(i)
                y_COT_SDA.append(MO2_U(i, *popt_SDA)/i)
    else:
        popt_SDA = [0,0]

    return x, y, x_COT, y_COT, x_SDA, y_SDA, x_COT_SDA, y_COT_SDA, popt_SDA

################################################################ Time2Hypo: If no current, how long before oxygen is zero ################################################################
def Plot_2_calc(SMR, EXP, SDA, O2refvol, FDEN, x_SDA, y_SDA, SigmoList):
    # Calculate Time 2 hypoxia when fish are resting
    x_TIME2LIM,y_TIME2LIM = Time2Hypo(SMR, O2refvol, FDEN)
    # Calculate Time 2 hypoxia when fish are swimming at Uopt
    MO2_Uopt = MO2_U(1/EXP, SMR, EXP)
    x_TIME2LIM_Uopt,y_TIME2LIM_Uopt = Time2Hypo(MO2_Uopt, O2refvol, FDEN)
    # Calculate Time 2 hypoxia when fish are swimming at Uopt, but reduce swimming speed when oxygen reaches limit
    MO2_Uopt = MO2_U(1/EXP, SMR, EXP)
    x_TIME2LIM_Uopt_Adv, y_TIME2LIM_Uopt_Adv = Time2HypoAdv(MO2_Uopt, O2refvol, FDEN, SigmoList, SMR, EXP)


    if SDA != 0:
        # find the fit for the SDA exponential function
        popt_SDA, _ = curve_fit(MO2_U, x_SDA, y_SDA)
        x_TIME2LIM_SDA,y_TIME2LIM_SDA = Time2Hypo(popt_SDA[0], O2refvol, FDEN)
        MO2_Uopt_SDA = MO2_U(1/popt_SDA[1], *popt_SDA)
        x_TIME2LIM_Uopt_SDA,y_TIME2LIM_Uopt_SDA = Time2Hypo(MO2_Uopt_SDA, O2refvol, FDEN)
        x_TIME2LIM_Uopt_Adv_SDA, y_TIME2LIM_Uopt_Adv_SDA = Time2HypoAdv(MO2_Uopt_SDA, O2refvol, FDEN, SigmoList, popt_SDA[0], popt_SDA[0])
    else:
        popt_SDA = [0,0]

    
    
    x_TIME2LIM = [x/3600 for x in x_TIME2LIM]
    x_TIME2LIM_SDA = [x/3600 for x in x_TIME2LIM_SDA]
    x_TIME2LIM_Uopt = [x/3600 for x in x_TIME2LIM_Uopt]
    x_TIME2LIM_Uopt_SDA = [x/3600 for x in x_TIME2LIM_Uopt_SDA]
    x_TIME2LIM_Uopt_Adv = [x/3600 for x in x_TIME2LIM_Uopt_Adv]
    x_TIME2LIM_Uopt_Adv_SDA = [x/3600 for x in x_TIME2LIM_Uopt_Adv_SDA]
    
    y_TIME2LIM = [x/1000 for x in y_TIME2LIM]
    y_TIME2LIM_SDA = [x/1000 for x in y_TIME2LIM_SDA]
    y_TIME2LIM_Uopt = [x/1000 for x in y_TIME2LIM_Uopt]
    y_TIME2LIM_Uopt_SDA = [x/1000 for x in y_TIME2LIM_Uopt_SDA]
    y_TIME2LIM_Uopt_Adv = [x/1000 for x in y_TIME2LIM_Uopt_Adv]
    y_TIME2LIM_Uopt_Adv_SDA = [x/1000 for x in y_TIME2LIM_Uopt_Adv_SDA]

    Time2LIM_Inter, Time2LIM_slope = regMaxCage(np.array(x_TIME2LIM),np.array(y_TIME2LIM))
    Time2LIM_SDA_Inter, Time2LIM_SDA_slope = regMaxCage(np.array(x_TIME2LIM_SDA),np.array(y_TIME2LIM_SDA))
    Time2LIM_Uopt_Inter, Time2LIM_Uopt_slope = regMaxCage(np.array(x_TIME2LIM_Uopt),np.array(y_TIME2LIM_Uopt))
    Time2LIM_Uopt_SDA_Inter, Time2LIM_Uopt_SDA_slope = regMaxCage(np.array(x_TIME2LIM_Uopt_SDA),np.array(y_TIME2LIM_Uopt_SDA))

    Time2LimXList = [x_TIME2LIM, x_TIME2LIM_SDA, x_TIME2LIM_Uopt, x_TIME2LIM_Uopt_SDA, x_TIME2LIM_Uopt_Adv, x_TIME2LIM_Uopt_Adv_SDA]
    Time2LimYList = [y_TIME2LIM, y_TIME2LIM_SDA, y_TIME2LIM_Uopt, y_TIME2LIM_Uopt_SDA, y_TIME2LIM_Uopt_Adv, y_TIME2LIM_Uopt_Adv_SDA]
    Time2LimInterList = [Time2LIM_Inter, Time2LIM_SDA_Inter, Time2LIM_Uopt_Inter, Time2LIM_Uopt_SDA_Inter]
    Time2LimSlopeList = [Time2LIM_slope, Time2LIM_SDA_slope, Time2LIM_Uopt_slope, Time2LIM_Uopt_SDA_slope]
    
    #return x_TIME2LIM,x_TIME2LIM_SDA,y_TIME2LIM,y_TIME2LIM_SDA, x_TIME2LIM_Uopt, x_TIME2LIM_Uopt_SDA, y_TIME2LIM_Uopt,y_TIME2LIM_Uopt_SDA
    return Time2LimXList, Time2LimYList, Time2LimInterList, Time2LimSlopeList
################################################################ Oxygen dist through cage: How does oxygen drop through the cage. Flow and swim speed change independently. #################
def Plot_3_calc(BLS, SMR, EXP, DIAM, O2refvol, VELO, FDEN, popt_SDA, SDA, SigmoList):
    # 1. First we need to know the current velocity in cm/s and then convert that to m/s to fit with further calculations
    Time2Replen1m = 1/(VELO/100) # Time2Replen1m gives us the time needed in order to replenish 1 meter of water
    MO2_U_Consumpt = (MO2_U(BLS, SMR, EXP))/3600*FDEN*Time2Replen1m # 2. MO2_U is Oxygen consumption pr second pr m3 pr replen time
    MO2_U_Consumpt_SDA = MO2_U_Consumpt
    if SDA != 0:
        MO2_U_Consumpt_SDA = (MO2_U(BLS, *popt_SDA))/3600*FDEN*Time2Replen1m
    x_meters = np.arange(0, DIAM, 1) # This is just the distance across the cage
    y_O2_Con_size = [] # list
    y_O2_Con_size_SDA = [] # list
    MO2_U_Calc = MO2_U(BLS, SMR, EXP) # Oxygen consumption
    MO2_U_Calc_SDA = MO2_U(BLS, *popt_SDA) # Oxygen consumption with SDA
    UnfedO2Con = O2refvol*1000 # Start concentration pr m3
    fedO2Con = O2refvol*1000 # Start concentration pr m3
    SS = BLS # Swimming speed
    SSSDA = BLS # Swimming speed
    SwimmingSpeed = [] # list
    SwimmingSpeedSDA = []
    for M in x_meters:
        pO2Calc = (20.94/(O2refvol*1000))*UnfedO2Con
        pO2CalcSDA = (20.94/(O2refvol*1000))*fedO2Con
        MaxMO2 = SigmaSoid(pO2Calc, *SigmoList)
        MaxMO2SDA = SigmaSoid(pO2CalcSDA, *SigmoList)

        if MO2_U_Calc >= MaxMO2: # If the scope is lower than the used oxygen, find a new swimming speed
            SS = Rev_MO2_U(MaxMO2, SMR, EXP) # Using the inverse MO2_U function, the speed equivalent to the maximum oxygen consumption is calculated
            if SS <= 0:
                SS = 0
            SwimmingSpeed.append(SS)
            MO2_U_Calc = MO2_U(SS, SMR, EXP)
            MO2_U_Consumpt = (MO2_U(SS, SMR, EXP))/3600*FDEN*Time2Replen1m
            UnfedO2Con = UnfedO2Con-MO2_U_Consumpt
        else:
            SwimmingSpeed.append(SS)
            UnfedO2Con = UnfedO2Con-MO2_U_Consumpt
            
        
        if MO2_U_Calc_SDA >= MaxMO2SDA: # If the scope is lower than the used oxygen, find a new swimming speed
            SSSDA = Rev_MO2_U(MaxMO2SDA, *popt_SDA) # Using the inverse MO2_U function, the speed equivalent to the maximum oxygen consumption is calculated
            if SSSDA <= 0:
                SSSDA = 0
            SwimmingSpeedSDA.append(SSSDA)
            MO2_U_Calc_SDA = MO2_U(SSSDA, *popt_SDA)
            MO2_U_Consumpt_SDA = (MO2_U(SSSDA, *popt_SDA))/3600*FDEN*Time2Replen1m
            fedO2Con = fedO2Con-MO2_U_Consumpt_SDA
        else:
            SwimmingSpeedSDA.append(SSSDA)
            fedO2Con = fedO2Con-MO2_U_Consumpt_SDA
               
        y_O2_Con_size.append(UnfedO2Con)
        y_O2_Con_size_SDA.append(fedO2Con)

    y_O2_Con_size = [x/1000 for x in y_O2_Con_size]
    y_O2_Con_size_SDA = [x/1000 for x in y_O2_Con_size_SDA]

    Con_size_inter, Con_size_slope = regMaxCage(np.array(x_meters),np.array(y_O2_Con_size))
    Con_size_SDA_inter, Con_size_SDA_slope = regMaxCage(np.array(x_meters),np.array(y_O2_Con_size_SDA))
    Con_size_List = [Con_size_inter, Con_size_slope, Con_size_SDA_inter, Con_size_SDA_slope]
    return x_meters, y_O2_Con_size, y_O2_Con_size_SDA, Con_size_List, SwimmingSpeed

def Plot_4_calc(x, y, x_SDA, y_SDA, SDA, EXP, SMR, FLEN, O2refvol, RangePos, FDEN,popt_SDA):
    # x is swimmingspeed in BL/s
    x_cm = [xi*FLEN for xi in x]
    x_BLs = [xi*FLEN for xi in x]
    # x_cm is swimmingspeed in cm/s
    x_m = [xi*FLEN/100 for xi in x]
    # x_m is swimmingspeed in m/s
    
    x_cm_SDA = [xi*FLEN for xi in x_SDA]
    # x_cm_SDA is swimmingspeed in cm/s

    # y is MO2_U pr h
    y_swim = [yi/3600 for yi in y]
    # y_swim is MO2_U pr sec
    y_swim_SDA = [yi/3600 for yi in y_SDA]
    # y_swim_SDA is MO2_U pr sec

    # declear a list for y values
    ReplenList = []

    for i in np.arange(0, len(x_cm), 1):
        # 1. Find the time it takes for the water to replenish the target section i.e. the first meter for example
        if i != 0:
            Time2Replen = 100/x_cm[i]
            MO2_U_temp = ((y_swim[i]*FDEN)*Time2Replen)*RangePos
            Replen = O2refvol-(MO2_U_temp/1000)
            ReplenList.append(Replen)
        else:
            ReplenList.append(0)

    ReplenList_SDA = []
    for i in np.arange(0, len(x_cm_SDA), 1):
        if i != 0:
            Time2Replen = 100/x_cm_SDA[i]
            MO2_U_temp_SDA = ((y_swim_SDA[i]*FDEN)*Time2Replen)*RangePos
            Replen_SDA = O2refvol-(MO2_U_temp_SDA/1000)
            ReplenList_SDA.append(Replen_SDA)
        else:
            ReplenList_SDA.append(0)

    ReplenList_Uopt = []
    MO2_Uopt = MO2_U((1/EXP), SMR, EXP)

    for i in np.arange(0, len(x_cm), 1):
        if i != 0:
            Time2Replen = 100/x_cm[i]
            if x_cm[i] <= (1/EXP)*FLEN:
                MO2_U_temp = ((MO2_Uopt/3600)*FDEN*Time2Replen)*RangePos
            else:
                MO2_U_temp = ((y_swim[i]*FDEN)*Time2Replen)*RangePos
            # 2. replenish water with flow
            Replen = O2refvol-(MO2_U_temp/1000)
            ReplenList_Uopt.append(Replen)
        else:
            ReplenList_Uopt.append(0)

    ReplenList_Uopt_SDA = []
    if SDA == 0:
        popt_SDA = [SMR, EXP]
    
    MO2_Uopt_SDA = MO2_U((1/popt_SDA[1]), popt_SDA[0], popt_SDA[1])

    for i in np.arange(0, len(x_cm_SDA), 1):
        if i != 0:
            Time2Replen = 100/x_cm_SDA[i]
            if x_cm_SDA[i] <= (1/EXP)*FLEN:
                MO2_U_temp = ((MO2_Uopt_SDA/3600)*FDEN*Time2Replen)*RangePos
            else:
                MO2_U_temp = ((y_swim_SDA[i]*FDEN)*Time2Replen)*RangePos
            # 2. replenish water with flow
            Replen = O2refvol-(MO2_U_temp/1000)
            ReplenList_Uopt_SDA.append(Replen)
        else:
            ReplenList_Uopt_SDA.append(0)

    return x_cm, x_cm_SDA, ReplenList, ReplenList_SDA, ReplenList_Uopt, ReplenList_Uopt_SDA


def make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2refvol, FLEN, DIAM, VELO, BLS, RangePos, SigmoList, threshold):  
    
    UcritMO2 = MO2_U(Ucrit, SMR, EXP)
    SigmoList[0] = UcritMO2
    #x_cm, x_cm_SDA, ReplenList, ReplenList_SDA, ReplenList_Uopt, ReplenList_Uopt_SDA = Plot_calc(SMR, EXP, Ucrit, SDA, FDEN, O2refvol, FLEN, DIAM, VELO, BLS, RangePos)

    # Get the threshold for food energy
    Thresh = (threshold/100)*O2refvol
    # Get data
    # for plot 1
    x,y,x_COT,y_COT,x_SDA, y_SDA,x_COT_SDA, y_COT_SDA, popt_SDA = Plot_1_calc(SMR, EXP, Ucrit, SDA)
    # for plot 2
    #x_TIME2LIM,x_TIME2LIM_SDA,y_TIME2LIM,y_TIME2LIM_SDA, x_TIME2LIM_Uopt, x_TIME2LIM_Uopt_SDA, y_TIME2LIM_Uopt,y_TIME2LIM_Uopt_SDA = Plot_2_calc(SMR, EXP, SDA, O2refvol, FDEN, x_SDA, y_SDA)
    Time2LimXList, Time2LimYList, Time2LimInterList, Time2LimSlopeList = Plot_2_calc(SMR, EXP, SDA, O2refvol, FDEN, x_SDA, y_SDA, SigmoList)
    # for plot 3
    x_meters, y_O2_Con_size, y_O2_Con_size_SDA, Con_size_List, SwimmingSpeed = Plot_3_calc(BLS, SMR, EXP, DIAM,O2refvol, VELO, FDEN, popt_SDA, SDA,SigmoList)
    # for plot 4
    x_cm, x_cm_SDA,ReplenList, ReplenList_SDA, ReplenList_Uopt, ReplenList_Uopt_SDA = Plot_4_calc(x, y, x_SDA, y_SDA, SDA, EXP, SMR, FLEN, O2refvol, RangePos, FDEN,popt_SDA)

    #Time2Hypo(SMR, y_SDA[0], O2refvol, f_dens)
    # data for plot 3
    # SMR - done
    # SMR_SDA = y_SDA[0]
    # MO2_Uopt: Add Uopt to MO2_U function. It will return the consumption

    # Generate plot for swimming energetics
    s1 = figure(plot_height=200,sizing_mode='scale_width', y_axis_label='MO2 (mg O2/kg/h)', x_range=(0, max(x)+0.1), y_range=(0, max(y)+10), tools='save, wheel_zoom, reset')
    s1.title.text = "A. Oxygen consumption and Cost Of Transport."
    s1.line(x, y, line_width=2, color="black", legend_label="MO2 U - Not fed")
        
    s1.legend.location = 'top_left'
    s1.legend.padding = 3
    s1.legend.label_text_font_size = '10pt'
    s1.xgrid.grid_line_color = None
    s1.ygrid.grid_line_color = None
    #s1.toolbar_location = None
    #s1.xaxis.visible = False
    #s1.outline_line_color = None
    s1.xaxis.major_label_text_font_size = '0pt'
    
    #N = 100
    #labels = ['point {0}'.format(i + 1) for i in range(N)]
    #tooltip = mpld3.plugins.PointLabelTooltip(x, labels=labels)
    #mpld3.plugins.connect(s1, tooltip)

    # Generate plot Cost of Transport
    s2 = figure(plot_height=220, sizing_mode='scale_width', x_axis_label='Swimming speed (BL/s)', y_axis_label='MO2 (mg O2/kg/BL)', x_range=(0, max(x_COT)+0.1), y_range=(0, max(y_COT)+10), tools='save, wheel_zoom, reset')
    s2.xgrid.grid_line_color = None
    s2.ygrid.grid_line_color = None
    s2.outline_line_color = None

    s2.legend.padding = 3
    s2.legend.label_text_font_size = '10pt'
    s2.line(x_COT, y_COT, line_width=2, color="black", legend_label="COT - Not fed")
    s2.line([(1/EXP),(1/EXP)],[0,max(y_COT)*0.4], color="black", line_width=2, line_dash ="dashed", legend_label="Uopt - not fed")

    source = ColumnDataSource({
        'base':[0,max(Time2LimXList[0])],
        'baseSDA':[0,x_cm[-1]],
        'baseMAX':[0,x_meters[-1]],
        'lower70':[O2refvol*0.7,O2refvol*0.7],
        'upper70':[O2refvol,O2refvol],
        'lower40':[O2refvol*0.4,O2refvol*0.4],
        'upper40':[O2refvol*0.7,O2refvol*0.7],
        'lower20':[O2refvol*0.2,O2refvol*0.2],
        'upper20':[O2refvol*0.4,O2refvol*0.4],
        'lower0':[O2refvol*0,O2refvol*0],
        'upper0':[O2refvol*0.2,O2refvol*0.2]
        })


    ConsList = np.linspace(0,max(Time2LimYList[0])+0.1,10000)
    ConsList = ConsList.reshape(int(len(ConsList)/10),10)
    onePercent = (max(Time2LimYList[0])+0.1)/100
    airsatList = ConsList/onePercent
    
    data = dict(Cons=[ ConsList ],
                airsat = [ airsatList ],
                x=[0],
                y=[0],
                dw=[max(Time2LimXList[0])],
                dh=[max(Time2LimYList[0])+0.1])

    TOOLTIPS = [
        ("Time (h):", "$x"),
        ("Oxygen (mg O2/L)", "@Cons"),
        ("Oxygen (% airsat)", "@airsat")
    ]
    
    def reverse_Me(x):
        return x[::-1]
    
    MyPal = reverse_Me(Turbo256)
    #s6 = figure(tools='hover,wheel_zoom', tooltips=TOOLTIPS)
    
    #s6.image(source=data, image='image', x='x', y='y', dw='dw', dh='dh', palette="Turbo256", alpha=0.8)#, palette="Plasma")

    s3 = figure(title="B. No current. Oxygen concentration over time", plot_height=350, sizing_mode='scale_width', x_axis_label='Time (h)', y_axis_label='O2 conc (mg O2/L)', x_range=(0, max(Time2LimXList[0])), y_range=(0, max(Time2LimYList[0])+0.1), tools='save, wheel_zoom, reset')# tools='hover,wheel_zoom,save', tooltips=TOOLTIPS,
    s3.xgrid.grid_line_color = None
    s3.ygrid.grid_line_color = None
    
    # Time2LimXList, Time2LimYList,
    #s3.image(source=data, image='Cons', x='x', y='y', dw='dw', dh='dh', palette=MyPal, alpha=0.8)
    #s3.line([0,max(x_TIME2LIM)],[onePercent*70,onePercent*70], color = "red",line_width=2, line_dash="dotted", legend_label="70% O2 limit")
    #s3.line([0,max(Time2LimXList[0])],[onePercent*70,onePercent*70], color = "red",line_width=2, line_dash="dotted", legend_label="70% O2 limit")
    

    thresholdlines3 = Span(location=Thresh, dimension='width', line_color='red', line_width=2, line_dash ="dotdash")
    s3.add_layout(thresholdlines3)
    s3.line([], [], legend_label='DO Threshold', line_dash='dotdash', line_color="red", line_width=2)
    s3.line(Time2LimXList[4],Time2LimYList[4], line_width=3, color="blue", line_dash ="dotted", legend_label="Limited")
    s3.line(Time2LimXList[5],Time2LimYList[5], line_width=3, color="blue", line_dash ="dotted")
    s3.line(Time2LimXList[0],Time2LimYList[0], line_width=2, color="black", legend_label="@Rest")
    
    # s3.line(O2refvol)
    if SDA != 0:
        s3.line(Time2LimXList[1],Time2LimYList[1], line_width=2, color="black", line_dash ="dashed", legend_label="@Rest_Fed")
    s3.line(Time2LimXList[2],Time2LimYList[2], line_width=2, color="blue", legend_label="@Uopt")
    if SDA != 0:
        s3.line(Time2LimXList[3],Time2LimYList[3], line_width=2, color="blue", line_dash ="dashed", legend_label="@Uopt_Fed")
    
    s3.legend.label_text_font_size = '8pt'
    s3.legend.location = "top_right"
    s3.legend.orientation = "vertical"
    s3.legend.padding = 4
    #s3.toolbar_location = None

    band70 = Band(base='base', lower='lower70', upper='upper70', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="green")
    band40 = Band(base='base', lower='lower40', upper='upper40', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="yellow")
    band20 = Band(base='base', lower='lower20', upper='upper20', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="orange")
    band0 = Band(base='base', lower='lower0', upper='upper0', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="red")
    s3.add_layout(band70)
    s3.add_layout(band40)
    s3.add_layout(band20)
    s3.add_layout(band0)


    TOOLTIPS = [
        ("meters into cage:", "$x"),
        ("Oxygen (mg O2/L):", "@Cons"),
        ("Oxygen (% airsat):", "@airsat")
    ]

    data = dict(Cons=[ ConsList ],
            airsat = [ airsatList ],
            x=[0],
            y=[0],
            dw=[max(x_meters[1:])+0.1],
            dh=[max(Time2LimYList[0])+0.1])


    s4 = figure(title="D. Oxygen distribution through cage. Adjust current and swimming speed in 5.",plot_height=300, sizing_mode='scale_width', x_axis_label='Cage (m)', y_axis_label='O2 conc (mg O2/L)',tools='wheel_zoom,save', x_range=(0, max(x_meters[1:])+0.1), y_range=(0,O2refvol))#, tools='hover,wheel_zoom,save',tooltips=TOOLTIPS)
    # Setting the second y axis range name and range
    thresholdlines4 = Span(location=Thresh, dimension='width', line_color='red', line_width=2, line_dash ="dotdash")
    s4.add_layout(thresholdlines4)
    s4.line([], [], legend_label='DO Threshold', line_dash='dotdash', line_color="red", line_width=2)
    s4.extra_y_ranges = {"foo": Range1d(start=0, end=max(SwimmingSpeed)+1)}
    s4.add_layout(LinearAxis(y_range_name="foo", axis_label="Swimming speed Bl/s"), 'right')
    s4.line(x_meters, SwimmingSpeed, line_width=2, color="green", legend_label="Swim speed", y_range_name="foo")
    
    #s4.image(source=data, image='Cons', x='x', y='y', dw='dw', dh='dh', palette=MyPal, alpha=0.8)
    #s4.line([0,max(x_meters)+0.1],[onePercent*70,onePercent*70], color = "red",line_width=2, line_dash="dotted", legend_label="70% O2 limit")
    s4.line(x_meters, y_O2_Con_size, line_width=2, color="purple", legend_label="[O2]")
    

    if SDA != 0:
        s4.line(x_meters, y_O2_Con_size_SDA, line_width=2, color="purple", line_dash ="dashed", legend_label="[O2] - fed")
    s4.xgrid.grid_line_color = None
    s4.ygrid.grid_line_color = None
    #s4.toolbar_location = None
    s4.legend.location = 'bottom_center'
    s4.legend.orientation = "horizontal"
    s4.legend.label_text_font_size = '8pt'
    s4.legend.padding = 4

    band70MAX = Band(base='baseMAX', lower='lower70', upper='upper70', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="green")
    band40MAX = Band(base='baseMAX', lower='lower40', upper='upper40', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="yellow")
    band20MAX = Band(base='baseMAX', lower='lower20', upper='upper20', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="orange")
    band0MAX = Band(base='baseMAX', lower='lower0', upper='upper0', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="red")
    s4.add_layout(band70MAX)
    s4.add_layout(band40MAX)
    s4.add_layout(band20MAX)
    s4.add_layout(band0MAX)

    #import bokeh.models as bkm
    #import bokeh.plotting as bkp

    #source = bkm.ColumnDataSource(data=your_frame)
    #p = bkp.figure(tools='add the tools you want here, but no hover!')
    #g1 = bkm.Cross(x='col1', y='col2')
    #g1_r = p.add_glyph(source_or_glyph=source, glyph=g1)
    #g1_hover = bkm.HoverTool(renderers=[g1_r],
    #                        tooltips=[('x', '@col1'), ('y', '@col2')])
    #p.add_tools(g1_hover)

    TOOLTIPS = [
        ("Velocity (cm/s):", "$x"),
        ("Oxygen (mg O2/L):", "@Cons"),
        ("Oxygen (% airsat):", "@airsat")
    ]

    data = dict(Cons=[ ConsList ],
        airsat = [ airsatList ],
        x=[0],
        y=[0],
        dw=[max(x_cm)+0.1],
        dh=[max(Time2LimYList[0])+0.1])

    s5 = figure(title="C. Oxygen content at outflow with changing swimmingspeed and current velocity", plot_height=300, sizing_mode='scale_width', x_axis_label='Swimming and current velocity (cm/s)', y_axis_label='O2 conc (mg O2/L)',tools=',wheel_zoom,save', x_range=(0, max(x_cm[1:])+0.1), y_range=(0,O2refvol)) #,tools='hover,wheel_zoom,save', tooltips=TOOLTIPS
    #s5.image(source=data, image='Cons', x='x', y='y', dw='dw', dh='dh', palette=MyPal, alpha=0.8)
    #s5.line([0,max(x_cm)+0.1],[onePercent*70,onePercent*70], color = "red",line_width=2, line_dash="dotted", legend_label="70% O2 limit")
    thresholdlines5 = Span(location=Thresh, dimension='width', line_color='red', line_width=2, line_dash ="dotdash")
    s5.add_layout(thresholdlines5)
    s5.line([], [], legend_label='DO Threshold', line_dash='dotdash', line_color="red", line_width=2)
    s5.line(x_cm[1:], ReplenList[1:], line_width=2, color="black", legend_label="@flow speed")
    s5.line(x_cm[1:], ReplenList_Uopt[1:], line_width=2, color="blue", legend_label="@Uopt")

    if SDA != 0:
        s5.line(x_cm_SDA[1:], ReplenList_SDA[1:], line_width=2, color="black", line_dash ="dashed", legend_label="@flow speed fed")   
        s5.line(x_cm_SDA[1:], ReplenList_Uopt_SDA[1:], line_width=2, color="blue", line_dash ="dashed", legend_label="@Uopt_fed")

    s5.legend.location = 'bottom_center'
    s5.legend.orientation = "horizontal"
    s5.legend.label_text_font_size = '8pt'
    s5.legend.padding = 4
    s5.xgrid.grid_line_color = None
    s5.ygrid.grid_line_color = None

    band70SDA = Band(base='baseSDA', lower='lower70', upper='upper70', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="green")
    band40SDA = Band(base='baseSDA', lower='lower40', upper='upper40', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="yellow")
    band20SDA = Band(base='baseSDA', lower='lower20', upper='upper20', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="orange")
    band0SDA = Band(base='baseSDA', lower='lower0', upper='upper0', source=source, level='underlay', fill_alpha=0.3, line_width=1, line_color='black',fill_color="red")
    s5.add_layout(band70SDA)
    s5.add_layout(band40SDA)
    s5.add_layout(band20SDA)
    s5.add_layout(band0SDA)
      
    #s6.line(x_cm[1:], ReplenList_Uopt[1:], line_width=4, color="black", legend_label="@Uopt")
    #s6.line(x_cm[1:], ReplenList[1:], line_width=2, color="blue", legend_label="@flow speed")



    # fed fish
    if SDA != 0:
        # MO2
        s1.line(x_SDA, y_SDA, line_width=2, color="red", legend_label="MO2 U - fed")
        # COT
        s2.line(x_COT_SDA, y_COT_SDA, line_width=2, color="red", legend_label="COT - fed")
        # Uopt
        s2.line([(1/popt_SDA[1]),(1/popt_SDA[1])],[0,max(y_COT)*0.4], color="red", line_width=2, line_dash ="dashed", legend_label="Uopt - fed")

        # Calculate Uopt fed fish
        UoptFed = round(1/popt_SDA[1],2)
    else:
        UoptFed = round(1/EXP,2)

    PC1 = column(s1, s2)

    plot = column(PC1, s3, s5, s4)


    script_MO2_U, div_MO2_U = components(plot)

    return script_MO2_U, div_MO2_U, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List

