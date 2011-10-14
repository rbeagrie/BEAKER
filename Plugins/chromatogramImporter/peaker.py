import beaker,os, csv
from types import *
import matplotlib.pyplot as plt
from scipy import stats
import scipy, numpy, re

class series_importer():
    def __init__(self,files):
        self.files = files
        print 'Files to import:'

        for f in self.files:
            print f

        self.species = []

    def set_times(self,times):
        self.times = times

    def import_files(self,start=False):
        self.data = []
        for f in self.files:
            self.data.append(chromatography_importer(f,start=start))

    def check_parameters(self,data_key,baseline=False,threshold=False,minima=False):
        self.data[data_key].set_parameters(baseline,threshold,minima)
        self.data[data_key].plot_peaks()

    def assign_data(self,time,intensity):
        for i in self.data:
            i.assign_data(time,intensity)

    def get_peak_list(self):
        total_peaks = set()

        for i in self.data:
            
            i.find_peaks()

            for p in i.peaks:
                total_peaks.add('%.2f  ' % p.centre[0])

        pks = list(total_peaks)

        for i in range(len(pks)):
            pks[i] = float(pks[i])

        pks.sort()

        return pks

    def print_peaks(self):

        for i,q in enumerate(self.data):
            q.find_peaks()

            line = 'Time: %i -- ' % self.times[i]

            for p in q.peaks:
                line += '%.2f  ' % p.centre[0]

            print line

        line = 'All Peaks: '
        ap = self.get_peak_list()
        for p in ap:
            line += '%.2f  ' % p

        print line

    def add_species(self,point,precision=2,name=False):
        self.species.append(species(point,precision,name))

    def add_species_list(self,species,names=False,precision=2):
        if names:
            for i,p in enumerate(species):
                self.add_species(p,precision,names[i])
        else:
            for p in species:
                self.add_species(p,precision)

    def find_species(self):
        self.add_species_list(self.get_peak_list())

    def fill_species(self):
        unassigned_peaks = []
        for i,q in enumerate(self.data):
            q.find_peaks()
            for p in q.peaks:
                for s in self.species:
                    ass = False
                    if s.check(p,self.times[i]):
                        ass = True
                        break
                if not ass:
                    unassigned_peaks.append(p)
            for s in self.species:
                s.fill(self.times[i])
        return unassigned_peaks

    def get_data(self):
        data = {}
        data['time'] = self.times
        for s in self.species:
            data[s.name] = []
            for t in self.times:
                data[s.name].append(s.data[t])
        return data

    def print_table(self):
        d = self.get_data()
        line = ''
        k = d.keys()
        k.sort()
        k.insert(0,k.pop())
        for h in k:
            line += '%s\t' % h
        print line
        for i in range(len(d[h])):
            line = ''
            for h in k:
                line += '%.2f\t' % d[h][i]
            print line
            
        

class chromatography_importer():
    def __init__(self,text_file,delimiter='\t',start=False):

        """Convert text_file to a dictionary object"""

        #logging.info('Importing data from %s' % text_file)

        assert type(text_file) is StringType, '"%s" is not a valid file name. File name must be a string.' % text_file

        #Check that the model file exists
        if not os.path.exists(text_file):
            raise beaker.BeakerException('Text file "%s" does not exist' % text_file)

        #Open the text file
        tfile = open(text_file,'r')
        #Pass it to the csv reader
        #logging.info('Parsing data in %s' % text_file)
        data = {}
        started = False
        header = False
        if start:
            for line in tfile:
                if started:
                    if header:
                        temp = line.strip('\n').split('\t')
                        temp = temp[:-1]
                        for i,t in enumerate(temp):
                            data[heads[i]].append(float(t))
                    else:
                        heads = line.strip('\n').split('\t')
                        for head in heads:
                            data[head] = []
                        header = True
                elif line == start + '\n':
                    started = True

        self.data = data

        self.threshold_value = 95
        self.baseline_value = 95
        self.minima_value = 4

    def assign_data(self,time,intensity):
        self.time = self.data[time]
        self.intensity = self.data[intensity]

    def plot_data(self):

        plt.plot(self.time,self.intensity)
        tmin = 0
        tmax = max(self.time)
        imarg = (max(self.intensity) - min(self.intensity))/2.5
        imax = max(self.intensity) + imarg
        imin = min(self.intensity) - imarg
        plt.axis([tmin,tmax,imin,imax])
        plt.show()

    def set_parameters(self,baseline=False,threshold=False,minima=False):
        if baseline:
            self.baseline_value = baseline
        if threshold:
            self.threshold_value = threshold
        if minima:
            self.minima_value = minima

    def find_threshold(self):
        
        return self.baseline+stats.scoreatpercentile(self.intensity,self.threshold_value)

    def find_baseline(self):
      
        nonpeaks = {}
        nonpeaks['time'] = []
        nonpeaks['intensity'] = []
        for i,v in enumerate(self.intensity):
            if v < stats.scoreatpercentile(self.intensity,self.baseline_value):
                nonpeaks['time'].append(self.time[i])
                nonpeaks['intensity'].append(self.intensity[i])
                    
        a_s,b_s,r,tt,stderr = stats.linregress(nonpeaks['time'],nonpeaks['intensity'])

        return a_s*numpy.array(self.time)+b_s

    def plot_peaks(self,savefile=False,raw=False):
                
        self.find_peaks() 
        
        plt.plot(self.time,self.intensity)
        if not raw:
            plt.plot(self.time,self.baseline)
            plt.plot(self.time,self.threshold)
            
            for i,p in enumerate(self.peaks):
                if i % 2:
                    color = '#FC8D59'
                else:
                    color = '#91BFDB'
                plt.fill_between(p.time,p.intensity,p.baseline,facecolor=color) 
                #plt.annotate('Peak %i: %.4f' % (i,p.area),p.centre)
        tmin = 0
        tmax = max(self.time)
        imarg = (max(self.intensity) - min(self.intensity))/2.5
        imax = max(self.intensity) + imarg
        imin = min(self.intensity) - imarg
        plt.axis([tmin,tmax,imin,imax])
        if savefile:
            plt.savefig(savefile)
            #print savefile
        else:
            plt.show()
        plt.cla()

    def find_peaks(self):
                

        self.baseline = self.find_baseline()

        self.threshold = self.find_threshold()

        self.find_minima()

        self.peaks = []
        inpeak = False
        for i in range(len(self.intensity)):
            if inpeak == False:
                if self.intensity[i] > self.threshold[i]:
                    inpeak = True
                    start = i
            elif self.intensity[i] < self.threshold[i]:
                self.peaks.append(Peak(start,i,self))
                inpeak = False
                

    def find_minima(self):
        pos = 0
        neg = 0
        pass_pos = False
        pass_neg = False
        self.minima = []
        self.maxima = []
        thresh = self.minima_value
        for i in range(1,len(self.intensity)):
            if (self.intensity[i] - self.intensity[i-1]) > 0:
                pos += 1
                neg = 0

                if pos > thresh:
                    pass_pos = True

                if pass_pos & pass_neg:
                    pass_neg = False
                    self.minima.append(i-(thresh+1))

            else:
                neg += 1
                pos = 0

                if neg > thresh:
                    pass_neg = True

                if pass_pos & pass_neg:
                    pass_pos = False
                    self.maxima.append(i-(thresh+1))

class Peak():
    def __init__(self,start,end,importer):
        self.start = start
        self.end = end
        self.importer = importer
        self.expand()
        self.fill()
        self.integrate()

    def expand(self):

        inpeak = True
        i = self.start
        while inpeak:
            if self.importer.intensity[i] < self.importer.baseline[i]:
                inpeak = False
                break
            elif i in self.importer.minima:
                inpeak = False
                break
            i -= 1
        self.start = i

        inpeak = True
        i = self.end
        while inpeak:
            if self.importer.intensity[i] < self.importer.baseline[i]:
                inpeak = False
                break
            elif i in self.importer.minima:
                inpeak = False
                break
            i += 1
        self.end = i

        inpeak = True
        i = self.start
        while inpeak:
            if i in self.importer.maxima:
                inpeak = False
                break
            i += 1
        self.centre = (self.importer.time[i],self.importer.intensity[i])

    def fill(self):
        self.intensity = []
        self.time = []
        self.baseline = []

        i = self.start

        while i < self.end:
            self.intensity.append(self.importer.intensity[i])
            self.time.append(self.importer.time[i])
            self.baseline.append(self.importer.baseline[i])
            i += 1

    def integrate(self):
        self.area = scipy.integrate.trapz(numpy.array(self.intensity)-numpy.array(self.baseline),self.time)

class species():
    def __init__(self,point,precision,name=False):
        if type(point) is FloatType:
            self.point = round(point,precision)
            self.start = self.point
        else:
            self.point = False
            self.start,self.end = point
            self.start = round(self.start,precision)
            self.end = round(self.end,precision)
        self.precision = precision
        if name:
            self.name = name
        else:
            self.name = self.start
        self.data = {}

    def check(self,peak,time):
        if self.point:
            if round(peak.centre[0],self.precision) == self.point:
                self.data[time] = float(peak.area)
                return True
            else:
                return False
        else:
            if (round(peak.centre[0],self.precision) >= self.start) and (round(peak.centre[0],self.precision) <= self.end):
                self.data[time] = float(peak.area)
                return True
            else:
                return False

    def fill(self,time):
        if not time in self.data:
            self.data[time] = 0.
                
            
        
#p = series_importer('C:\\Users\\Rob\\Dropbox\\Project\\HPLC\\2008 10 08.seq',match='2uM PNP\+1mM ADP\+1mM Mg .*\.TXT')
