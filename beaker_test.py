import beaker,unittest,numpy

class beaker_test(unittest.TestCase):

    def setUp(self):
        self.new = beaker.session('Nose Tests Project')

    def bad_model_file_test(self):
        mpath = 'C:\\Users\\Rob\\Desktop\\kinpy\\tests\\bisable.k'
        self.assertRaises(beaker.BeakerException,self.new.initiate_model,mpath)

    def ambiguous_model_file_test(self):
        mpath = 'C:\\Users\\Rob\\Desktop\\kinpy\\tests\\ambig_model_file'
        self.assertRaises(beaker.BeakerException,self.new.initiate_model,mpath)
        
    def kinpy_code_test(self):
        mpath = 'C:\\Users\\Rob\\BEAKER\\Fixtures\\kinpy_code.py'
        self.new.initiate_model(mpath)
        assert isinstance(self.new.model,beaker.model)
        
    def kinpy_model_test(self):
        mpath = 'C:\\Users\\Rob\\BEAKER\\Fixtures\\model.k'
        self.new.initiate_model(mpath)
        assert isinstance(self.new.model,beaker.model)

    def model_run_test(self):
        mpath = 'C:\\Users\\Rob\\BEAKER\\Fixtures\\model.k'
        self.new.initiate_model(mpath)
        run_result = self.new.model.run(self.new.model.kinpy_model.debug_y0,[0,1,2],self.new.model.kinpy_model.debug_k)
        fixture = fix = numpy.loads('\x80\x02cnumpy.core.multiarray\n_reconstruct\nq\x01cnumpy\nndarray\nq\x02K\x00\x85U\x01b\x87Rq\x03(K\x01K\x03K\x0c\x86cnumpy\ndtype\nq\x04U\x02f8K\x00K\x01\x87Rq\x05(K\x03U\x01<NNNJ\xff\xff\xff\xffJ\xff\xff\xff\xffK\x00tb\x89T \x01\x00\x00\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?\x00\x00\x00\x00\x00\x00\xe0?G.e\x8e\xcd\x83\xe5?\x97~i\nY\xf9\xde?\xbeJ\no\xa8\xe0\xd6?\xdeE\r\x82\xa2\x1c\xe8?G.e\x8e\xcd\x83\xe5?\x97~i\nY\xf9\xde?\xbeJ\no\xa8\xe0\xd6?\xdeE\r\x82\xa2\x1c\xe8?.~\xb1\x04\xc5\xfd\xe3? \x9d\x94>:\x15\xe1?.~\xb1\x04\xc5\xfd\xe3? \x9d\x94>:\x15\xe1?\xa5G_~\xcb\xe1\xe7?X-\xdb\xaf\xea\xb1\xdc?\x81\xd9\xa4\x86\xbe\x16\xd6?\x9d\xec9\xb1\xfc\xf3\xe8?\xa5G_~\xcb\xe1\xe7?X-\xdb\xaf\xea\xb1\xdc?\x81\xd9\xa4\x86\xbe\x16\xd6?\x9d\xec9\xb1\xfc\xf3\xe8?s\xa4+\x0e|E\xe5?\x1cX\x94V/V\xe1?s\xa4+\x0e|E\xe5?\x1cX\x94V/V\xe1?tb.')
        assert (run_result == fixture).all()
        

    def tearDown(self):
        import shutil
        shutil.rmtree(self.new.directory)
