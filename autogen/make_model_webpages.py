#!/usr/bin/env python
from pdrtpy.modelset import ModelSet
from pdrtpy.plot.modelplot import ModelPlot
from multiprocessing import Pool,Manager
import numpy.ma as ma
import os
import jinja2
from copy import deepcopy
import argparse

def init_processes(l):
    global lock
    lock = l

class Page():
    def __init__(self):
        self.env=jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        self.base_dir = "../models"

    def write_all_models_page(self,all_models,all_names):
        # don't instantiate these in __init__ or you get a 
        # "TypeError: cannot pickle weakref" from Pool.starmap
        self.allmodelstemplatefile = 'all_models_page_jinja_template.html'
        self.allmodelstemplate = self.env.get_template(self.allmodelstemplatefile)
        #reverse sort so wolfire/kaufman comes first
        wkfirst = dict(reversed(sorted(list(all_models.items()))))
        names = dict(reversed(sorted(list(all_names.items()))))
        #for key,value in wkfirst.items():
        #    print(key)
        output=self.allmodelstemplate.render(all_models=wkfirst,all_names=names)
        fh = open(f'{self.base_dir}/index.html','w')
        fh.write(output)
        fh.close()

    def make_page(self,all_models,all_names,lock,quick=False):
        # check all models.tab files and existence of all therein
        t = ModelSet.all_sets()
        z = zip(list(t["name"]),list(t["z"]),list(t["medium"]),list(t["mass"]))
        
        if False:
            print("single threading...")
            for name,metallicity,medium,mass in z:
                self.process_modelset(name,metallicity,medium,mass)
        else:
            print("pooling...")
            pool = Pool(os.cpu_count()-2,initializer=init_processes,initargs=(lock,))
            pool.starmap(self.process_modelset,z)

    def process_modelset(self,n,z,md,m):
        debug = False
        if debug and n != "wk2006": return
        print(f'Making page for {n,z,md,m}')
        explain = dict()
        explain["lmc"] = 'The models in the wk2006 Large Magellanic Cloud ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
        explain["smc"] = 'The models in the wk2006 Small Magellanic Cloud ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
        explain["wk2006"] = 'The models in the wk2006 ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
        explain["wk2020"] = 'The models in the wk2020 ModelSet are based on <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>, <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2010ApJ...716.1191W/abstract">Wolfire et al. 2010</a>, and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2016ApJ...826..183N/abstract">Neufeld &amp; Wolfire 2016</a>. They use <a class="mya" href="/models.html#2020">these parameters.</a> More details are in the FITS headers.'
        explain["kt2013"] = 'The models in this ModelSet were created with the <a class="mya" href="https://astro.uni-koeln.de/stutzki/research/kosma-tau">KOSMA-tau</a> PDR code. More details are in the FITS headers.'
        model_title = dict()
        model_title["wk2006"] = "Wolfire/Kaufman 2006"
        model_title["smc"] = "Wolfire/Kaufman 2006 Small Magellanic Cloud "
        model_title["lmc"] = "Wolfire/Kaufman 2006 Large Magellanic Cloud"
        model_title["wk2020"] = "Wolfire/Kaufman 2020"
        model_title["kt2013"] = "KOSMA-tau 2013"

        success = True
        failed = list()
        pagetemplatefile = 'model_page_jinja_template.html'
        pagetemplate = self.env.get_template(pagetemplatefile)
        indextemplatefile = 'index_page_jinja_template.html'
        indextemplate = self.env.get_template(indextemplatefile)

        ms = ModelSet(name=n,z=z,medium=md,mass=m)
        if ms.code == 'KOSMA-tau':
            ms.keyname = "kt2013"
        else:
            ms.keyname = n
        ms.tarball = f"/models/{ms.keyname}_models.tgz"
        ms.header = ms.description.replace("$A_V$","A<sub>V</sub>").replace("$R_V$","R<sub>V</sub>").replace("M$_\odot$", "M<sub>&odot;</sub>")
        if m is None or ma.is_masked(m):
            ms.dir = f'{n}_Z{z}_{md}'
        else:
            ms.dir = f'{n}_Z{z}_{md}_M{m}'
        ms.dir = ms.dir.replace(' ','_')
        with lock:
            all_models[ms.dir] = ms.header
            all_names[ms.dir] = n
        if quick: 
            return

        os.mkdir(f'{self.base_dir}/{ms.dir}')
        mp = ModelPlot(ms)
        # stop complaining about too many figures
        mp._plt.rcParams.update({'figure.max_open_warning': 0})

        i = 0
        numcols = 4
        table_contents = "<tr>"
        for r in ms.table["ratio"]:
            if i !=0 and i%numcols == 0:
                table_contents+="</tr>\n<tr>"
            try:
                model=ms.get_model(r)
                modelfile = ms.table.loc[r]["filename"]
                if "/" in model._title:
                    model._title += " Intensity Ratio"
                else:
                    if "FIR" not in model._title and "Surface" not in  model._title and "A_V" not in model._title:
                        model._title += " Intensity"
                model._title = model._title.replace("$\mu$","&micro;").replace("$_{FIR}$","<sub>FIR</sub>").replace("$_2$","<sub>2</sub>").replace("$A_V$","A<sub>V</sub>").replace("$^{13}$","<sup>13</sup>").replace("$A_V=0.01$","A<sub>V</sub> = 0.01")
                                        #.replace("$T_S$","T<sub>S</sub>")
                #print(f"doing {r} = {modelfile} , {modelfile}.png , title={model._title} CTYPE=[{model.wcs.wcs.ctype[0]},{model.wcs.wcs.ctype[1]}]")
                if "$" in model._title:
                    print(f"############ OOPS missed some latex {model._title}")
                fig_out = f'{ms.dir}/{modelfile}.png'
                fig_html = f'{ms.dir}/{modelfile}.html'
                fits_out = f'{ms.dir}/{modelfile}.fits'
                f_html = f'{modelfile}.html'
                table_contents += f'<td><a href="{f_html}">{model._title}</a></td>'
                i = i+1
                if model.wcs.wcs.ctype[0] == "T_e":
                    # Iron line ratios are function of electron temperature and electron density
                    # not H2 density and radiation field.
                    mp.plot(r,label=True,legend=False,
                            norm="zscale",cmap='plasma')
                else:
                    mp.plot(r,yaxis_unit="Habing",label=True, legend=False,
                            norm="zscale",cmap='plasma')
                mp.savefig(f'{self.base_dir}/{fig_out}')
                model.write(f'{self.base_dir}/{fits_out}')
                # This is supposed to stop complaints about 
                # too many figures, but actually does not!
                mp._plt.close(mp.figure) 
                output=pagetemplate.render(model=model,
                                       fitsfilename=f'{modelfile}.fits',
                                       model_explain=explain[ms.keyname],
                                       modelfile=modelfile)
                fh = open(f'{self.base_dir}/{fig_html}','w')
                fh.write(output)
                #print(f'{self.base_dir}/{fig_html}')
               # print(output)
               # print("===========================================")
                fh.close()

            except FileNotFoundError:
                raise
            except Exception as e:
                raise
                success = False
                failed.append(f'{r} {modelfile} : {str(e)}\n')
        if not success:
            print("Couldn't open these models:",failed)
        table_contents += '</tr>'
        output=indextemplate.render(modelset=ms,
                                    table_contents=table_contents)
        
        fh = open(f'{self.base_dir}/{ms.dir}/index.html','w')
        fh.write(output)
        fh.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CLI.')
    parser.add_argument('-q','--quick',help='skip creating plots, just update all_models page',action="store_true")
    args = parser.parse_args()
    if args.quick:
        quick = True
    else:
        quick = False
    manager = Manager()
    all_models = manager.dict()
    all_names = manager.dict()
    lock = manager.Lock()
    p = Page()
    print("using quick = ",quick)
    p.make_page(all_models,all_names,lock,quick=quick)
    p.write_all_models_page(all_models,all_names)
