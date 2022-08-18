#!/usr/bin/env python
# PDR Toolbox script to generate ionized gas line diagnostic plots
# Requires pdrtpy package. (pip install pdrtpy)
# https://dustem.astro.umd.edu/hiiregion
# Send comments, questions, and currency to Marc Pound mpound@umd.edu

from pdrtpy.measurement import Measurement
from pdrtpy.modelset import ModelSet
from pdrtpy.plot.modelplot import ModelPlot
import astropy.units as u

ms = ModelSet(name="wk2020",z=1)
mp = ModelPlot(ms)
mp.phasespace(["ARIII_21.83/ARIII_8.99","ARV_13.07/ARV_7.91"],nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))

mp.savefig("ARIII_21.83_8.99-ARV_13.07_7.91.png",dpi=600)
mp.savefig("ARIII_21.83_8.99-ARV_13.07_7.91.pdf")

mp.phasespace(['FEII_1.60/FEII_1.64','FEII_1.64/FEII_5.34'],
              nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))
mp.savefig("FeII_1.60_1.64-1.64_5.34.png",dpi=600)
mp.savefig("FeII_1.60_1.64-1.64_5.34.pdf")

mp.phasespace(['FEII_5.67/FEII_5.34','FEII_1.64/FEII_5.34'],
              nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))
mp.savefig("FeII_5.67_5.34-1.64_5.34.png",dpi=600)
mp.savefig("FeII_5.67_5.34-1.64_5.34.pdf")

mp.phasespace(['FEII_17.94/FEII_5.34','FEII_1.64/FEII_5.34'],
              nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))
mp.savefig("FeII_17.94_5.34-1.64_5.34.png",dpi=600)
mp.savefig("FeII_17.94_5.34-1.64_5.34.pdf")

mp.phasespace(['FEII_1.60/FEII_1.64','FEII_22.90/FEII_5.34'],
              nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))
mp.savefig("FeII_1.60_1.64-22.90_5.34.png",dpi=600)
mp.savefig("FeII_1.60_1.64-22.90_5.34.pdf")

mp.phasespace(['FEII_1.60/FEII_1.64','FEII_26/FEII_5.34'],reciprocal=[False,False],
              nax2_clip=[10,1E6]*u.Unit("cm-3"),nax1_clip=[2E3,1E4]*u.Unit("K"))
mp.savefig("FeII_1.60_1.64-25.99_5.34.png",dpi=600)  
mp.savefig("FeII_1.60_1.64-25.99_5.34.pdf")
