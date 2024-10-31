; Sequence name: BC6S6P
; Setup:
;   - single battery voltage range 15V - 25.2V
;   - charge current 12A per pack
;   - discharge current 12A per pack
;   - 6 battery packs in parallel, 1 pack in series


    #a=100                  ; number of cycles to run
    #c=0                    ; current cycle, starts at 0

setup:
    sc=0                    ; set source current to 0 A
    scn=0                   ; set sink current to 0 A
    sp=3000                 ; set source power to 3 kW
    spn=-3000               ; set sink power to 3 kW
    sv=25.2                 ; set source voltage to 25.2 V to reduce leakage current
    w=10                    ; wait ten seconds

charge:
    inc sc,0.72             ; increase current by 720 mA
    w=0.01                  ; wait 10 ms for 72 A/s ramp
    cjl sc,72,charge        ; continue ramping current up to 72 A
    sc=72                   ; set source current to 72 A
    w=0.1                   ; wait 100 ms for current to settle

cloop:
    cjl mc,0.9,cend         ; jump to cend if measured current is less than 900 mA
    jp cloop                ; otherwise, continue charge loop

cend:
    sc=0                    ; set source current to 0 A

    cje #a,0,exit           ; jump to exit if number of remaining cycles is 0
    w=600                   ; wait ten minutes
    sv=12                   ; set source voltage to 12 V

discharge:
    dec scn,0.72            ; decrease sink current by 720 mA
    w=0.01                  ; wait 10 ms for -72 A/s ramp
    cjg scn,-72,discharge   ; continue ramping current to -72 A
    scn=-72                 ; set sink current to -72 A
    inc #c,1                ; increment current cycle number
    w=0.1                   ; wait 100 ms for voltage to settle

dloop:
    cjl mv,18,dend          ; jump to dend if measured voltage is less than 18 V
    jp dloop                ; otherwise, continue discharge loop

dend:
    scn=0                   ; set sink current to 0 A
    sv=25.2                 ; set source voltage to 25.2 V to reduce leakage current

    w=1200                  ; wait 20 minutes

    dec #a,1                ; decrement number of remaining cycles
    jp charge               ; jump to charge loop

exit:
    w=86400                 ; wait for a day
    end
