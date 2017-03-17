import xlwt
from win32com.client import DispatchEx


class ExcelHelper:
    def __init__(self,log = None):
        self.log = log

    def _def_font(self):
        font = xlwt.Font()
        font.name ='Arial'
        font.bold =True
        font.height = 8*20
        return font

    def _def_cell_style(self):
        style = xlwt.XFStyle()
        style.alignment.wrap = 1
        style.alignment.vert = style.alignment.VERT_CENTER
        style.alignment.horz=style.alignment.HORZ_CENTER
        style.borders.left=style.borders.MEDIUM
        style.borders.top=style.borders.MEDIUM
        style.borders.right=style.borders.MEDIUM
        style.borders.bottom=style.borders.MEDIUM
        return style

    def _def_cell_pattern(self):
        pat = xlwt.Pattern()
        pat.pattern=xlwt.Pattern.SOLID_PATTERN
        pat.pattern_fore_colour = 42
        return pat

    def save_twod_array_to_excel(self,text,file_name,sheet_name,col_num_and_width=None):
        """
        Saves the data in two dimension array into excel file
        :param text: two dimension array containing the data
        :param file_name: path to save the excel file
        :param sheet_name: name of the sheet in excel file
        :param col_num_and_width: list of column number with it desiered width
        :return:
        """
        style = self._def_cell_style()
        style.font = self._def_font()

        workbook = xlwt.Workbook(encoding="utf8")
        worksheet = workbook.add_sheet(sheet_name)
        for x in range(1,len(text)):
            for y in range(0,len(text[0])):
                #print str(text[x][y])
                worksheet.write(x,y,(str(text[x][y]).decode("cp1251").encode("utf8")),style)
        style.pattern=self._def_cell_pattern()
        for y in range(0,len(text[0])):
            worksheet.write(0,y,(str(text[0][y])),style)
        for x in range(1,len(text)):
            worksheet.row(x).height_mismatch = True
            worksheet.row(x).height = 60*20
        if col_num_and_width is not None:
            for x in col_num_and_width:
                worksheet.col(x[0]).width = x[1]
        workbook.save(file_name)

    def add_filter(self,file_name,sheet_name):
        xl = DispatchEx('Excel.Application')
        xl.Workbooks.Open(file_name)
        xl.ActiveWorkbook.Worksheets(sheet_name).Columns("A:Z").AutoFilter(1)
        xl.ActiveWorkbook.Close(SaveChanges=1)
        xl.Quit()