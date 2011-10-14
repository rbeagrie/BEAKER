import peaker
p = peaker.series_importer('C:\\Users\\Rob\\Dropbox\\Project\\HPLC\\2008 10 08.seq',match='2uM PNP\+1mM ADP\+1mM Mg .*\.TXT')
p.set_times([0,2,12,22,32])
p.import_files('Raw Data:')
p.assign_data('Time(min)','Value(mAU)')
p.data[0].set_parameters(95,92,4)
p.data[1].set_parameters(95,76,3)
p.data[2].set_parameters(95,82,4)
p.data[3].set_parameters(95,82,3)
p.data[4].set_parameters(95,80,3)
#p.print_peaks()
p.add_species_list([(3.17,3.19),
                    4.27,
                    (4.72,4.73),
                    (5.07,5.09),
                    5.37,
                    (5.59,5.60),
                    5.79,
                    5.95],

                   ['ADP',
                    'A2',
                    'A3',
                    'A4',
                    'A5',
                    'A6',
                    'A7',
                    'A8'])
up = p.fill_species()
#print up
d = p.get_data()
#print d
p.print_table()
'''
test = peaker.chromatography_importer('C:\\Users\\Rob\\Dropbox\\Project\\HPLC\\2010 04 30.seq\\33 - polymerisation PNPfl t=1 rep2.TXT',start='Raw Data:')
test.assign_data('Time(min)','Value(mAU)')
test.plot_peaks()'''
