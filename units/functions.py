# -*- coding: utf-8 -*-
# !/usr/bin/env python
import cv2
import math
import numpy as np

# colormath numpy 2.x uyumluluk fix'i
if not hasattr(np, "asscalar"):
    np.asscalar = lambda x: x.item()

from colormath.color_diff import delta_e_cie1976, delta_e_cie1994, delta_e_cie2000, delta_e_cmc
from colormath.color_objects import LabColor
from skimage.color import rgb2lab, lab2lch

def VideoOperation():
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while True:
        _, frame = capture.read()
        cv2.imshow('Press the "q" key to capture an image.', frame)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            break
    resized = cv2.resize(frame, (320,240))
    w, h, _ = resized.shape
    return frame, cv2.cvtColor(resized, cv2.COLOR_BGR2RGB), h, w

def RgbCalculator(frame):
    imagergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    r = list()
    g = list()
    b = list()
    [(r.append(y[0]),g.append(y[1]),b.append(y[2])) for x in imagergb for y in x]
    return [sum(r)/len(r), sum(g)/len(g), sum(b)/len(g)]

def LabCHCalculator(frame):
    imagergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagelab = rgb2lab(imagergb)
    imagelch = lab2lch(imagelab)
    L = list()
    a = list()
    b = list()
    C = list()
    H = list()
    [(L.append(y[0]),a.append(y[1]),b.append(y[2])) for x in imagelab for y in x]
    [(C.append(y[1]),H.append(y[2])) for x in imagelch for y in x]
    return [sum(L)/len(L), sum(a)/len(a), sum(b)/len(b), sum(C)/len(C), (sum(H) * 57.289071045)/len(H)]

def DeltaCalculator(CIE, LabCH, delta):
    lab_reference  = LabColor(lab_l=CIE[0], lab_a=CIE[1],lab_b=CIE[2])
    lab = LabColor(lab_l=LabCH[0], lab_a=LabCH[1], lab_b=LabCH[2])
    if delta == 'delta_e_cie1976':
        return delta_e_cie1976(lab, lab_reference)
    elif delta == 'delta_e_cie1994':
        return delta_e_cie1994(lab, lab_reference)
    elif delta == 'delta_e_cie2000':
        return delta_e_cie2000(lab, lab_reference)
    else:
        return delta_e_cmc(lab, lab_reference)
