@app.route('/model/', methods=['GET', 'POST'])
def calc():
    if request.method == 'POST':
        Study = int(request.form["ddList"])
        if Study != 0:
            Temp, Sal, SMR, EXP, Ucrit, FLEN, FMASS = Database(Study)
        else:
            Temp = float(request.form['inputTemp'])
            Sal = float(request.form['inputSal'])
            SMR = float(request.form['inputSMR'])
            EXP = float(request.form['inputEXP'])
            Ucrit = float(request.form['inputUcrit'])
            FLEN = float(request.form['inputFLEN'])
            FMASS = float(request.form['inputFMASS'])

        SDA = float(request.form['inputSDA'])
        Uopt = round(1/EXP,2)
        VELO = float(request.form['inputVELO'])
        CIRC = float(request.form['inputCIRC'])
        DEPT = float(request.form['inputDEPT'])
        NUMFISH = int(request.form['inputNUMFISH'])
        BLS = float(request.form["inputBLS"])
        TMASS = round(FMASS*NUMFISH*1000)
        DIAM, RADI, VOL = calcCage(CIRC, DEPT)
        VOL = int(VOL)
        FDEN = round(TMASS/VOL, 1)
        O2envL = round(em.beta1atm(Temp, Sal),2) # mg/L
        O2envm3 = round(O2envL*1000,2)
        RangePos = 1
        Sigmo10 = [327.5, 6.5, 3.5]
        Sigmo15 = [414.9, 6.04, 5.514]
        Sigmo20 = [388.1, 6.24, 5.7]
        SigmoList = [Sigmo10, Sigmo15, Sigmo20]

        script, div, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List = plotz.make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2envL, FLEN, DIAM, VELO, BLS, RangePos, SigmoList[0])
            
        Time2RestList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 0)
        Time2RestFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 1)
        Time2UoptList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 2)
        Time2UoptFedList = Time2HypoFunc(Time2LimInterList, Time2LimSlopeList, 3)

        MaxLengthList = MaxLengthCage(Con_size_List[0], Con_size_List[1], DIAM)
        MaxLengthListSDA = MaxLengthCage(Con_size_List[2], Con_size_List[3], DIAM)

        cdn_js = CDN.js_files
        SS = round(BLS * FLEN,1)

        return render_template('index.html', script=script, div=div, cdn_js=cdn_js[0],
            SMR=SMR, EXP=EXP, Ucrit=Ucrit, Uopt=Uopt, SDA=SDA, UoptFed=UoptFed, Temp=Temp, Sal=Sal, VELO=VELO, 
            O2envL=O2envL, O2envm3=O2envm3, CIRC=CIRC, DEPT=DEPT, DIAM=DIAM, RADI=RADI, VOL=VOL, NUMFISH=NUMFISH,
            FMASS=FMASS, FLEN=FLEN, TMASS=TMASS, FDEN=FDEN, BLS=BLS, SS=SS, Study=Study, Time2RestList=Time2RestList, 
            Time2RestFedList=Time2RestFedList, Time2UoptList=Time2UoptList, Time2UoptFedList=Time2UoptFedList, 
            MaxLengthList=MaxLengthList, MaxLengthListSDA=MaxLengthListSDA)

    return render_template('index.html')



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
    
    RangePos = request.form.get('inputRangePos', 1, type=int)
    O2envL = round(em.beta1atm(Temp, Sal),2) # mg/L
    SDA = request.form.get('inputSDA', 0, type=float)
    CIRC = request.form.get('inputCIRC', 0, type=float)
    DEPT = request.form.get('inputDEPT', 0, type=float)
    DIAM, RADI, VOL = calcCage(CIRC, DEPT)  
    VELO = request.form.get('inputVELO', 0, type=float)
    BLS = request.form.get('inputBLS', 0, type=float)
    NUMFISH = request.form.get('inputNUMFISH', 0, type=int)
    TMASS = (NUMFISH*1000)*FMASS
    FDEN = round(TMASS/VOL, 1)
    Sigmo10 = [327.5, 6.5, 3.5]
    Sigmo15 = [414.9, 6.04, 5.514]
    Sigmo20 = [388.1, 6.24, 5.7]
    SigmoList = [Sigmo10, Sigmo15, Sigmo20]
    
    SCRIPT, DIV, UoptFed, Time2LimInterList, Time2LimSlopeList, Con_size_List = plotz.make_plot(SMR, EXP, Ucrit, SDA, FDEN, O2envL, FLEN, DIAM, VELO, BLS, RangePos, SigmoList[0])
        
    return render_template('update_content.html', DIV=DIV, SCRIPT=SCRIPT)
