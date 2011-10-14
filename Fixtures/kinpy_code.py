from scipy import *
import scipy.integrate as itg

'''
## Reaction ##

#Bistable reaction. See Chapter 10, Book of GENESIS.

Sx + X <-> SxX
SxX <-> Px + X

Sy + Y <-> SyY
SyY <-> Py + Y 

Yi + Px <-> Yia
Yia + Px <-> Y

Xi + Py <-> Xia
Xia + Py <-> X

Px <-> Sx
Py <-> Sy

## Mapping ##

Sx	0	 -1*v_0(y[2], y[1], y[0]) +1*v_8(y[3], y[0])
X	1	 -1*v_0(y[2], y[1], y[0]) +1*v_1(y[2], y[1], y[3]) +1*v_7(y[11], y[7], y[1])
SxX	2	 +1*v_0(y[2], y[1], y[0]) -1*v_1(y[2], y[1], y[3])
Px	3	 +1*v_1(y[2], y[1], y[3]) -1*v_4(y[8], y[3], y[9]) -1*v_5(y[5], y[3], y[9]) -1*v_8(y[3], y[0])
Sy	4	 -1*v_2(y[5], y[4], y[6]) +1*v_9(y[4], y[7])
Y	5	 -1*v_2(y[5], y[4], y[6]) +1*v_3(y[5], y[6], y[7]) +1*v_5(y[5], y[3], y[9])
SyY	6	 +1*v_2(y[5], y[4], y[6]) -1*v_3(y[5], y[6], y[7])
Py	7	 +1*v_3(y[5], y[6], y[7]) -1*v_6(y[11], y[10], y[7]) -1*v_7(y[11], y[7], y[1]) -1*v_9(y[4], y[7])
Yi	8	 -1*v_4(y[8], y[3], y[9])
Yia	9	 +1*v_4(y[8], y[3], y[9]) -1*v_5(y[5], y[3], y[9])
Xi	10	 -1*v_6(y[11], y[10], y[7])
Xia	11	 +1*v_6(y[11], y[10], y[7]) -1*v_7(y[11], y[7], y[1])
'''

class reaction_model():

    def dy(self, y, t, k):

        #Sx + X <-> SxX
        v_0 = lambda SxX, X, Sx : k0 * Sx**1 * X**1 - k0r * SxX**1
        k0 = k[0]
        k0r = k[1]

        #SxX <-> Px + X
        v_1 = lambda SxX, X, Px : k1 * SxX**1 - k1r * Px**1 * X**1
        k1 = k[2]
        k1r = k[3]

        #Sy + Y <-> SyY
        v_2 = lambda Y, Sy, SyY : k2 * Sy**1 * Y**1 - k2r * SyY**1
        k2 = k[4]
        k2r = k[5]

        #SyY <-> Py + Y 
        v_3 = lambda Y, SyY, Py : k3 * SyY**1 - k3r * Py**1 * Y**1
        k3 = k[6]
        k3r = k[7]

        #Yi + Px <-> Yia
        v_4 = lambda Yi, Px, Yia : k4 * Yi**1 * Px**1 - k4r * Yia**1
        k4 = k[8]
        k4r = k[9]

        #Yia + Px <-> Y
        v_5 = lambda Y, Px, Yia : k5 * Yia**1 * Px**1 - k5r * Y**1
        k5 = k[10]
        k5r = k[11]

        #Xi + Py <-> Xia
        v_6 = lambda Xia, Xi, Py : k6 * Xi**1 * Py**1 - k6r * Xia**1
        k6 = k[12]
        k6r = k[13]

        #Xia + Py <-> X
        v_7 = lambda Xia, Py, X : k7 * Xia**1 * Py**1 - k7r * X**1
        k7 = k[14]
        k7r = k[15]

        #Px <-> Sx
        v_8 = lambda Px, Sx : k8 * Px**1 - k8r * Sx**1
        k8 = k[16]
        k8r = k[17]

        #Py <-> Sy
        v_9 = lambda Sy, Py : k9 * Py**1 - k9r * Sy**1
        k9 = k[18]
        k9r = k[19]

        return array([\
         -1*v_0(y[2], y[1], y[0]) +1*v_8(y[3], y[0]),\
         -1*v_0(y[2], y[1], y[0]) +1*v_1(y[2], y[1], y[3]) +1*v_7(y[11], y[7], y[1]),\
         +1*v_0(y[2], y[1], y[0]) -1*v_1(y[2], y[1], y[3]),\
         +1*v_1(y[2], y[1], y[3]) -1*v_4(y[8], y[3], y[9]) -1*v_5(y[5], y[3], y[9]) -1*v_8(y[3], y[0]),\
         -1*v_2(y[5], y[4], y[6]) +1*v_9(y[4], y[7]),\
         -1*v_2(y[5], y[4], y[6]) +1*v_3(y[5], y[6], y[7]) +1*v_5(y[5], y[3], y[9]),\
         +1*v_2(y[5], y[4], y[6]) -1*v_3(y[5], y[6], y[7]),\
         +1*v_3(y[5], y[6], y[7]) -1*v_6(y[11], y[10], y[7]) -1*v_7(y[11], y[7], y[1]) -1*v_9(y[4], y[7]),\
         -1*v_4(y[8], y[3], y[9]),\
         +1*v_4(y[8], y[3], y[9]) -1*v_5(y[5], y[3], y[9]),\
         -1*v_6(y[11], y[10], y[7]),\
         +1*v_6(y[11], y[10], y[7]) -1*v_7(y[11], y[7], y[1]),\
         \
        ])

    def __init__(self):

        self.debug_y0 = array([\
        #Sx
        0.0,\
        #X
        0.0,\
        #SxX
        0.0,\
        #Px
        0.0,\
        #Sy
        0.0,\
        #Y
        0.0,\
        #SyY
        0.0,\
        #Py
        0.0,\
        #Yi
        0.0,\
        #Yia
        0.0,\
        #Xi
        0.0,\
        #Xia
        0.0,\
        ])

        

        self.debug_k = array([\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        1.0,\
        ])

        

        self.reactants = list([
        'Sx',
        'X',
        'SxX',
        'Px',
        'Sy',
        'Y',
        'SyY',
        'Py',
        'Yi',
        'Yia',
        'Xi',
        'Xia'])
        
    def run(self,y0,t,k):

        return itg.odeint(self.dy, y0, t, (k,))