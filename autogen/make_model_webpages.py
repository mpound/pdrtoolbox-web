#!/usr/bin/env python
from pdrtpy.modelset import ModelSet
from pdrtpy.plot.modelplot import ModelPlot
import numpy.ma as ma
import os
import jinja2

class Page():

    def make_page(self):
        debug = False
        explain = dict()
        explain["wk2006"] = 'The models in the wk2006 ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
        explain["wk2020"] = 'The models in the wk2020 ModelSet are based on <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>, <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2010ApJ...716.1191W/abstract">Wolfire et al. 2010</a>, and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2016ApJ...826..183N/abstract">Neufeld &amp; Wolfire 2016</a>. They use <a class="mya" href="/models.html#2020">these parameters.</a> More details are in the FITS headers.'
        explain["kt2013"] = 'The models in this ModelSet were created with the <a class="mya" href="https://astro.uni-koeln.de/stutzki/research/kosma-tau">KOSMA-tau</a> PDR code. More details are in the FITS headers.'
        model_title = dict()
        model_title["wk2006"] = "Wolfire/Kaufman 2006"
        model_title["wk2020"] = "Wolfire/Kaufman 2020"
        model_title["kt2013"] = "KOSMA-tau 2013"

        success = True
        # check all models.tab files and existence of all therein
        t = ModelSet.all_sets()
        failed = list()
        env=jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        pagetemplatefile = 'model_page_jinja_template.html'
        pagetemplate = env.get_template(pagetemplatefile)
        indextemplatefile = 'index_page_jinja_template.html'
        indextemplate = env.get_template(indextemplatefile)
        base_dir = "../models"
        table_contents = "<tr>"
        for n,z,md,m in zip(list(t["name"]),list(t["z"]),list(t["medium"]),list(t["mass"])):
            print(n,z,md,m)
            mdict = dict()
            if debug and n != "wk2006": continue
            ms = ModelSet(name=n,z=z,medium=md,mass=m)
            ms.tarball = f"/models/{n}_models.tgz"
            if m is not None:
                ms.header = f"{model_title[n]}, Z={z}, {md}"
            else:
                ms.header = f"{model_title[n]}, Z={z}, {md}, M={m} M<sub>&odot;</sub> "
            mp = ModelPlot(ms)
            # stop complaining about too many figures
            mp._plt.rcParams.update({'figure.max_open_warning': 0})
            print(f'Making page for {n,z,md,m}')
            if m is None or ma.is_masked(m):
                dir = f'{n}_Z{z}_{md}'
            else:
                dir = f'{n}_Z{z}_{md}_M{m}'
            dir = dir.replace(' ','_')
            os.mkdir(f'{base_dir}/{dir}')

            i = 0
            numcols = 4
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
                    #print(f"doing {r} = {modelfile}.png title={model._title}")
                    if "$" in model._title:
                        print(f"############ OOPS missed some latex {model._title}")
                    fig_out = f'{dir}/{modelfile}.png'
                    fig_html = f'{dir}/{modelfile}.html'
                    f_html = f'{modelfile}.html'
                    table_contents += f'<td><a href="{f_html}">{model._title}</a></td>'
                    mdict[r] = fig_html
                    i = i+1
                    if model.wcs.wcs.ctype[0] == "T_e":
                        # Iron line ratios are function of electron temperature and electron density
                        # not H2 density and radiation field.
                        mp.plot(r,label=True,legend=False,
                                norm="log",cmap='plasma')
                    else:
                        mp.plot(r,yaxis_unit="Habing",label=True, legend=False,
                                norm="log",cmap='plasma')
                    mp.savefig(f'{base_dir}/{fig_out}')
                    # This is supposed to stop complaints about 
                    # too many figures, but actually does not!
                    mp._plt.close(mp.figure) 
                    fh = open(f'{base_dir}/{fig_html}','w')
                    output=pagetemplate.render(model=model,
                                           fitsfilename=f'{modelfile}.fits',
                                           model_explain=explain[n],
                                           modelfile=modelfile)
                    fh.write(output)
                    #print(f'{base_dir}/{fig_html}')
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
            fh = open(f'{base_dir}/{dir}/index.html','w')
            output=indextemplate.render(modelset=ms,
                                        table_contents=table_contents)
            
            fh.write(output)
            fh.close()

    def make_aux_page(self):
        pass

if __name__ == '__main__':
    p = Page()
    p.make_page()