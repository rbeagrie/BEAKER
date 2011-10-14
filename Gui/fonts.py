import tkFont, Tkinter

class Fonts():
    def __init__(self):

        self.default = tkFont.Font(font='TkDefaultFont',name='BkDefaultFont')

        self.bold = tkFont.Font(font='BkDefaultFont',name='BkBold')
        self.bold['weight'] = 'bold'

        self.large = tkFont.Font(font='BkDefaultFont',name='BkLarge')
        self.large['size'] += 1

        self.large_bold = tkFont.Font(font='BkLarge',name='BkLargeBold')
        self.large_bold['weight'] = 'bold'

        self.xlarge = tkFont.Font(font='BkLarge',name='BkXLarge')
        self.xlarge['size'] += 1

        self.xlarge_bold = tkFont.Font(font='BkXLarge',name='BkXLargeBold')
        self.xlarge_bold['weight'] = 'bold'

