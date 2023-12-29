import itertools
import pandas as pd

def return_gen_ed_section_capacity(exam_code, window):

    if window == 'January':
        if exam_code[0] == 'E':
            return 34
        else:
            return 40
    if window == 'June':
        if exam_code[0] == 'E':
            return 40
        else:
            return 34

def return_section_number(row):
    senior = row["senior?"]
    SWD = row["SWD?"]
    D75 = row["D75?"]
    ENL = row["ENL?"]

    time_and_a_half = row["time_and_a_half?"]
    double_time = row["double_time?"]
    QR = row["read_aloud?"]
    conflict = row["Conflict?"]

    scribe = row["scribe?"]
    one_on_one = row["one_on_one?"]
    Technology = row["Technology?"]
    large_print = row["large_print?"]



    if not SWD and not D75 and not ENL:
        if conflict:
            if senior:
                return 2
            else:
                return 3
        else:
            if senior:
                return 4
            else:
                return 5

    if scribe or Technology or one_on_one:
        return 89
    
    temp_str = ''
    for attribute in [senior,conflict,ENL,QR, time_and_a_half,double_time]:
        if attribute:
            temp_str+='1'
        else:
            temp_str+='0'
    

    section_dict = {
        '000010':24,
        '100010':31,
        '001010':32,
        '101010':33,
        '001000':34,
        '101000':35,
        '000001':36,
        '100001':37,
        '001001':38,
        '101001':39,
        '000110':40,
        '100110':43,
        '001110':44,
        '101110':45,
        '000101':46,
        '100101':47,
        '001101':48,
        '101101':49,
        '010010':50,
        '110010':51,
        '011010':52,
        '111010':53,
        '011000':54,
        '111000':55,
        '010001':56,
        '110001':57,
        '011001':58,
        '111001':59,
        '010110':62,
        '110110':63,
        '011110':64,
        '111110':65,
        '010101':66,
        '110101':67,
        '011101':68,
        '111101':69,
    }

    return section_dict.get(temp_str,20)



    if conflict and double_time and ENL and senior and QR:
        return 86
    if conflict and double_time and ENL and QR:
        return 87
    if conflict and double_time and senior and QR:
        return 85
    if conflict and double_time and QR:
        return 88

    if conflict and double_time and ENL and senior:
        return 82
    if conflict and double_time and ENL:
        return 83
    if conflict and double_time and senior:
        return 81
    if conflict and double_time:
        return 84

    if double_time and ENL and senior and QR:
        return 66
    if double_time and ENL and QR:
        return 67
    if double_time and senior and QR:
        return 65
    if double_time and QR:
        return 68

    if double_time and ENL and senior:
        return 62
    if double_time and ENL:
        return 63
    if double_time and senior:
        return 61
    if double_time:
        return 64

    if conflict and QR and ENL and senior:
        return 51
    if conflict and QR and time_and_a_half and senior:
        return 55
    if conflict and QR and ENL:
        return 52
    if conflict and QR and time_and_a_half:
        return 56

    if conflict and time_and_a_half and senior and ENL:
        return 35
    if conflict and time_and_a_half and senior:
        return 35
    if conflict and time_and_a_half and senior:
        return 35

    if QR and ENL and senior:
        return 41
    if QR and time_and_a_half and senior:
        return 45
    if QR and time_and_a_half:
        return 46



    
    if time_and_a_half and senior:
        return 25
    if time_and_a_half:
        return 26
    
    ## Checkvalve for Sped
    return 19
