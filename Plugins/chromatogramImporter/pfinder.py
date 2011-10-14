import peaker,os

path = 'C:\\Users\\Rob\\Dropbox\\Project\\HPLC\\2008 10 08.seq'

def getfiles(path):

    pstring = '['
    for p in os.listdir(path):
        pstring += '\'%s\',\n' % p

    pstring = pstring [:-2] + ']'

    print pstring

files = [
('18 - 2uM PNP+1mM ADP+1mM Mg t=0.TXT',92,4),
('19 - 2uM PNP+1mM ADP+1mM Mg t=2.TXT',76,3),
('20 - 2uM PNP+1mM ADP+1mM Mg t=12.TXT',82,4),
('21 - 2uM PNP+1mM ADP+1mM Mg t=22.TXT',82,3),
('22 - 2uM PNP+1mM ADP+1mM Mg t=32.TXT',80,3)]

times = [0,2,12,22,32]

savefiles = []

total_peaks = set()

for q,x in enumerate(files):

    f,t,m = x
                      
    i = peaker.chromatography_importer()
    i.import_text(os.path.join(path,f),start='Raw Data:')
    i.assign_data('Time(min)','Value(mAU)')

    root,ext = os.path.splitext(f)
    root += '.png'
    
    #i.plot_peaks(os.path.join(path,root))
    i.find_peaks(threshold=t,minima=m)
    line = 'Time = %is -- ' % times[q]

    for p in i.peaks:
        line += '%.2f  ' % p.centre[0]
        total_peaks.add('%.2f  ' % p.centre[0])

    print line

pks = list(total_peaks)

for i in range(len(pks)):
    pks[i] = float(pks[i])

pks.sort()

print '\n',pks
