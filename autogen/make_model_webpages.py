#!/usr/bin/env python
from pdrtpy.modelset import ModelSet
from pdrtpy.plot.modelplot import ModelPlot
from multiprocessing import Pool,Manager
import numpy.ma as ma
import os
import jinja2
import argparse
import sys
from pathlib import Path

EXPLAIN = dict()
EXPLAIN["lmc"] = 'The models in the wk2006 Large Magellanic Cloud ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
EXPLAIN["smc"] = 'The models in the smc ModelSet are based on <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>, <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2010ApJ...716.1191W/abstract">Wolfire et al. 2010</a>, and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2016ApJ...826..183N/abstract">Neufeld &amp; Wolfire 2016</a>. They use z=0.2 and <a class="mya" href="/models.html#2020">these parameters.</a> More details are in the FITS headers.'
EXPLAIN["wk2006"] = 'The models in the wk2006 ModelSet are based <a class="mya" href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=1999ApJ...527..795K" >Kaufman et al. 1999</a> and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>. They use <a class="mya" href="/models.html#parameters">these parameters.</a> More details are in the FITS headers.'
EXPLAIN["wk2020"] = 'The models in the wk2020 ModelSet are based on <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2006ApJ...644..283K/abstract" >Kaufman et al. 2006 </a>, <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2010ApJ...716.1191W/abstract">Wolfire et al. 2010</a>, and <a class="mya" href="https://ui.adsabs.harvard.edu/abs/2016ApJ...826..183N/abstract">Neufeld &amp; Wolfire 2016</a>. They use <a class="mya" href="/models.html#2020">these parameters.</a> More details are in the FITS headers.'
EXPLAIN["kt2013"] = 'The models in this ModelSet were created with the <a class="mya" href="https://astro.uni-koeln.de/stutzki/research/kosma-tau">KOSMA-tau</a> 2013 PDR code. More details are in the FITS headers.'
EXPLAIN["kt2020"] = 'The models in this ModelSet were created with the <a class="mya" href="https://astro.uni-koeln.de/stutzki/research/kosma-tau">KOSMA-tau</a> 2020 PDR code. The parameters were chosen to match as closely as possible those of the Wolfire-Kaufman 2020 models, so they may be more easily comparable. More details are in the FITS headers.'
EXPLAIN["hii"] = 'We assume that the line emission is in the optically thin limit so that the ratio of emissivities is given by the ratio of volume emissivity. For <span class="math notranslate nohighlight"> \({\\rm Ar^{+2}}\) </span>, and <span class="math notranslate nohighlight"> \({\\rm Ar^{+4}}\) </span>, we use CHIANTI ( <a class="mya" href="https://doi.org/10.1051/aas:1997368"> Dere et al (1997)</a>; <a class="mya" href="https://doi.org/10.3847/1538-4357/abd8ce"> DelZanna et al. (2022)</a>) using the default values for the A values and collision strengths.  For <span class="math notranslate nohighlight"> \({\\rm Fe^+}\) </span> we substituted the default values in CHIANTI with Einstein A values from <a class="mya" href="https://doi.org/10.1051/0004-6361/201118059"> Deb &amp; Hibbert (2011) </a> and collision strengths from <a class="mya" href="https://doi.org/10.1093/mnras/sty3198"> Smyth et al. (2019) </a>.  The emissivity ratios are found in the temperature range from <span class="math notranslate nohighlight"> \(T_e=10^3\) </span> K to <span class="math notranslate nohighlight"> \(10^4\) </span> K, and the density range from <span class="math notranslate nohighlight"> \(n_e = 10^2~{\\rm cm^{-3}}\) </span> to <span class="math notranslate nohighlight"> \(10^6~{\\rm cm^{-3}}\).  </span>'


def skip_modelset(n, kosmatau):
    if n.startswith("kt") and not kosmatau:
        print(f"skipping {n}")
        return True
    if n.startswith("lmc") or n.startswith("wk2006"):
        print(f"skipping {n}")
        return True
    return False


class Page():
    def __init__(self, kosmatau, modelset=None):
        self.env=jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        self.base_dir = Path("../models.new")
        self.kosmatau = kosmatau
        self.modelset = modelset
        self.base_dir.mkdir(exist_ok=True)
        # per-worker-process cache of (ModelSet,ModelPlot), populated lazily
        # in process_ratio() so consecutive ratio tasks for the same
        # ModelSet landing on the same forked worker skip re-loading the
        # FITS tables.
        self._ms_cache = dict()

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
        print("rendering all models...")
        output=self.allmodelstemplate.render(all_models=wkfirst,all_names=names)
        fh = open(f'{self.base_dir}/index.html','w')
        fh.write(output)
        fh.close()

    def selected_modelsets(self):
        t = ModelSet.all_sets()
        if self.modelset is not None:
            t = t[t["name"] == self.modelset]
            if len(t) == 0:
                print(f"no ModelSet found matching name '{self.modelset}'")
                return []
        ziplist = list(zip(list(t["name"]),list(t["z"]),list(t['losangle']),list(t["medium"]),list(t["mass"])))
        # normalize masked mass values to None so they're hashable (used as
        # part of the per-worker ModelSet cache key in process_ratio)
        ziplist = [(n,z,losangle,md,None if ma.is_masked(m) else m) for n,z,losangle,md,m in ziplist]
        return [spec for spec in ziplist if not skip_modelset(spec[0], self.kosmatau)]

    def register_modelset(self,n,z,losangle,md,m,all_models,all_names):
        """Build the ModelSet and register it in all_models/all_names. Cheap
        (no plotting) - safe to run serially in the main process."""
        ms = ModelSet(name=n,z=z,losangle=losangle,medium=md,mass=m)
        if n.startswith("kt2013"):
            ms.keyname = "kt2013"
        else:
            ms.keyname = n
        ms.tarball = f"/models/{ms.keyname}_models.tgz"
        ms.header = ms.description.replace("$A_V$","A<sub>V</sub>").replace("$R_V$","R<sub>V</sub>").replace("M$_\odot$", "M<sub>&odot;</sub>")
        if m is None or ma.is_masked(m):
            ms.dir = f'{n}_Z{z}_L{losangle}_{md}'
        else:
            # KT models don't have losangle
            ms.dir = f'{n}_Z{z}_{md}_M{m}'
        ms.dir = ms.dir.replace(' ','_')
        all_models[ms.dir] = ms.header
        all_names[ms.dir] = n
        return ms

    def make_page(self,all_models,all_names,quick=False,jobs=None):
        specs = self.selected_modelsets()

        if quick:
            # registration only, no plotting - not worth spinning up a Pool
            for n,z,losangle,md,m in specs:
                self.register_modelset(n,z,losangle,md,m,all_models,all_names)
            return

        ms_by_dir = dict()
        tasks = list()
        for n,z,losangle,md,m in specs:
            print(f'Making page for {n,z,losangle,md,m}')
            ms = self.register_modelset(n,z,losangle,md,m,all_models,all_names)
            ms_by_dir[ms.dir] = ms
            os.mkdir(f'{self.base_dir}/{ms.dir}')
            for r in ms.table["ratio"]:
                tasks.append((ms.dir,n,z,losangle,md,m,r))

        if jobs is None:
            jobs = os.cpu_count()
        print(f"pooling {len(tasks)} ratio tasks with jobs={jobs}")
        pool = Pool(jobs)
        results = pool.starmap(self.process_ratio,tasks)
        pool.close()
        pool.join()

        by_dir = dict()
        for ms_dir,success,table_cell,error in results:
            by_dir.setdefault(ms_dir,list()).append((success,table_cell,error))

        indextemplatefile = 'index_page_jinja_template.html'
        indextemplate = self.env.get_template(indextemplatefile)
        for ms_dir,ms in ms_by_dir.items():
            i = 0
            numcols = 4
            table_contents = "<tr>"
            failed = list()
            for success,table_cell,error in by_dir.get(ms_dir,[]):
                if success:
                    if i !=0 and i%numcols == 0:
                        table_contents+="</tr>\n<tr>"
                    table_contents += table_cell
                    i = i+1
                else:
                    failed.append(error)
            if failed:
                print("Couldn't open these models:",failed)
            table_contents += '</tr>'
            output=indextemplate.render(modelset=ms,
                                        table_contents=table_contents)
            fh = open(f'{self.base_dir}/{ms_dir}/index.html','w')
            fh.write(output)
            fh.close()

    def process_ratio(self,ms_dir,n,z,losangle,md,m,r):
        """Plot and write out a single model ratio. Returns
        (ms_dir, success, table_cell_html_or_None, error_or_None)."""
        key = (n,z,losangle,md,m)
        cached = self._ms_cache.get(key)
        if cached is None:
            ms = ModelSet(name=n,z=z,losangle=losangle,medium=md,mass=m)
            if n.startswith("kt2013"):
                ms.keyname = "kt2013"
            else:
                ms.keyname = n
            mp = ModelPlot(ms)
            # stop complaining about too many figures
            mp._plt.rcParams.update({'figure.max_open_warning': 0})
            self._ms_cache[key] = (ms,mp)
        else:
            ms,mp = cached

        pagetemplatefile = 'model_page_jinja_template.html'
        pagetemplate = self.env.get_template(pagetemplatefile)

        try:
            #ugly hack
            modelfile = ms.table.loc[r]["filename"]
            if modelfile  == "FEII25p99.fits":
                model=ms.get_model(r,unit="erg/(cm3 s ion)")
            else:
                model=ms.get_model(r)
            if "/" in model._title:
                #kluge for HII diagnotic files
                if "FE" in modelfile or "AR" in modelfile:
                    model._title += " Emissivity Ratio"
#@TODO set modeltype. but need to be able to handle it in Measurement/Modelset
                else:
                    model._title += " Intensity Ratio"
            else:
                if "FIR" not in model._title and "Surface" not in  model._title and "A_V" not in model._title:
                #kluge for HII diagnotic files
                    if "FE" in modelfile or "AR" in modelfile:
                        model._title += " Emissivity"
                    else:
                        model._title += " Intensity"
            model._title = model._title.replace("$ \mu","$\mu")
            model._title = model._title.replace("$\mu$","&micro;").replace("$_{FIR}$","<sub>FIR</sub>").replace("$_2$","<sub>2</sub>").replace("$A_V$","A<sub>V</sub>").replace("$^{13}$","<sup>13</sup>").replace("$A_V=0.01$","A<sub>V</sub> = 0.01")
                                    #.replace("$T_S$","T<sub>S</sub>")
            if "$" in model._title:
                print(f"############ OOPS missed some latex {model._title} in {ms.name} {modelfile}")
            fig_out = f'{ms_dir}/{modelfile}.png'
            fig_html = f'{ms_dir}/{modelfile}.html'
            fits_out = f'{ms_dir}/{modelfile}.fits'
            f_html = f'{modelfile}.html'
            table_cell = f'<td><a href="{f_html}">{model._title}</a></td>'
            if model.wcs.wcs.ctype[0] == "T_e":
                # Iron line ratios are function of electron temperature and electron density
                # not H2 density and radiation field.
                mp.plot(r,label=True,legend=False,
                        norm="zscale",cmap='plasma',aspect='auto')
                keyname = "hii"
                model.xaxis = "electron gas temperature <em>T<sub>e</sub></em>"
                model.yaxis = "electron density <em>n<sub>e</sub></em>"
                model.where = "from the ionized gas layer "
                model.viewingangle=""
            else:
                mp.plot(r,yaxis_unit="Habing",label=True, legend=False,
                        norm="zscale",cmap='plasma')
                keyname = ms.keyname
                model.where = "from the surface "
                model.xaxis = "cloud density <em>n</em>"
                model.yaxis = "the FUV flux incident on the cloud <em>G<sub>0</sub></em>"
                if ms.name=="wk2020" or ms.name=="smc":
                    model.viewingangle=f"The above model is at a viewing angle of i={losangle} degrees, where i=0 is face-on."
                else:
                    model.viewingangle=""
            mp.savefig(f'{self.base_dir}/{fig_out}')
            model.write(f'{self.base_dir}/{fits_out}')
            # This is supposed to stop complaints about
            # too many figures, but actually does not!
            mp._plt.close(mp.figure)
            output=pagetemplate.render(model=model,name=ms.name,
                                   fitsfilename=f'{modelfile}.fits',
                                   model_explain=EXPLAIN[keyname],
                                   modelfile=modelfile)
            fh = open(f'{self.base_dir}/{fig_html}','w')
            fh.write(output)
            fh.close()
            return (ms_dir,True,table_cell,None)

        except FileNotFoundError as fne:
            print(fne)
            return (ms_dir,False,None,f'{r} {modelfile} : {str(fne)}\n')
        except Exception as exc:
            print(exc)
            return (ms_dir,False,None,f'{r} {modelfile} : {str(exc)}\n')


if __name__ == '__main__':
    print(__name__)
#    warnings.simplefilter("ignore",DeprecationWarning)
#    warnings.simplefilter("ignore",UserWarning)
    parser = argparse.ArgumentParser(description='Create model webpages for PDR Toolbox website dustem.astro.umd.edu.', prog=sys.argv[0])
    parser.add_argument('-k','--kosmatau',help='do the kosma tau models',action="store_true",default=False)
    parser.add_argument('-m','--modelset',help='only do the given modelset',action="store",default=None)
    parser.add_argument('-q','--quick',help='skip creating plots, just update all_models page',action="store_true")
    parser.add_argument('-j','--jobs',help='number of worker processes to use (default: all cores)',action="store",type=int,default=None)
    args = parser.parse_args()

    if args.quick:
        quick = True
    else:
        quick = False
    manager = Manager()
    all_models = manager.dict()
    all_names = manager.dict()
    p = Page(kosmatau=args.kosmatau, modelset=args.modelset)
    print("using quick = ",quick)
    p.make_page(all_models,all_names,quick=quick,jobs=args.jobs)
    p.write_all_models_page(all_models,all_names)
