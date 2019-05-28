from __future__ import print_function
#the residual might be broken if the data and the fit have different lengths,they should

from numpy import array, mean, vstack, arange, genfromtxt, transpose, delete,sign,amax,zeros,append
from numpy import abs as npabs
import math

# this os import might be windows specific
from os import system,path
# from StringIO import StringIO
from io import BytesIO,open, StringIO
from PySide2 import QtCore, QtGui, QtWidgets
from matplotlib.figure import Figure
from PySide2.QtWidgets import QSizePolicy
from PySide2.QtCore import QSize, Signal
from matplotlib.backends.backend_qt5agg import (FigureCanvas as Canvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib import rcParams,gridspec
from matplotlib.ticker import MaxNLocator

from struct import unpack
#import time

# this is for windows, if on another OS will crash i guess
# if needed then remove the copy to clipboard
import win32clipboard as clipboard

# ABOVE ALL OF THE IMPORTS,A BIT MESY

# this is necessaty to be compatible in both python 2 and 3
try: 
	type(unicode)
except: 
	unicode = str

	
# defining some styling for the graphs
rcParams['font.size'] = 10
rcParams['font.weight'] = 'bold'
rcParams['axes.linewidth'] = 1.5
rcParams['xtick.major.width'] = 1.5
rcParams['ytick.major.width'] = 1.5
rcParams['xtick.minor.width'] = 1
rcParams['ytick.minor.width'] = 1
#rcParams['ytick.minor.size'] = 1
rcParams['legend.scatterpoints'] = 0
#rcParams['path.sketch'] = 1,100,10
rcParams['keymap.yscale'] = 'k'
#rcParams['keymap.yscale'] = 'k'


# defining in advance some variable
alpha=[]   #to store alpha values from the contin
distribution=[]   #to store the resulting distributions
fit=[]   #to store the resulting fits
residual=[]  #to store the resulting residuals
counter=0
data=array([[0.0001,1,0],[0,0,0]])   #the measurements go here
trace=[]  #to store the intensity trace
index=None
ut=1    #position of the upper boundary
lt=0.000001    #position of the lower boundary
check=False
x=0
y=0
counterfit=[]
peak=[]
rangea=''
rangeb=''
fileDialog=''   #location of the file to open
sut=0.0		# related to the boundaries
slt=1.0
fstar=1
dir=False
dual=False    #whether or not the data was measured in dual, meaning, 2 corelograms in the dataset, applicable to some formats
lense=False  #evacescent setup
stau=False # true=changed to s
threeD=False  #for the trace plot onthe 3d data
theta1=0   
theta2=90

# this class	should keep the boundaries in place,it is not really doing so though,
 # kind of useless and should be thought again
 # it only keeps the boundaries from going too far off the data
class Param:

	def __init__(self, initialValue=None, minimum=2e-8, maximum=3.4e+8):
		self.minimum = minimum
		self.maximum = maximum
		if initialValue != self.constrain(initialValue):
			raise ValueError('illegal initial value')
		self.value = initialValue
		
	# the constrains should be checked here too, and the min and max values should be set according to the dataset 
	def set(self, value):
		self.value = value
	
	def constrain(self, value):
		if value <= self.minimum:
			value = self.minimum
		if value >= self.maximum:
			value = self.maximum
		return value
		
# this class is necessary to accept drag and drop of filesin pyside2		
class drop(QtCore.QObject):
	ds = QtCore.Signal(list)
	
		
		# this is the graph
class MatplotlibWidget(Canvas):
	
	def __init__(self, parent=None,
				 width=4, height=3, dpi=100):   
		global fileDialog

		self.figure = Figure(figsize=(width, height), dpi=dpi)
		Canvas.__init__(self, self.figure)
		self.setParent(parent)
		self.state= ''	
		Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
		Canvas.updateGeometry(self)
		self.lt = Param(1e-6)
		self.ut = Param(10)			
		# self.figure.canvas.mpl_connect('button_press_event', self.mouseDown)##callbacks.connect
		self.figure.canvas.mpl_connect('pick_event', self.mouseDown)##callbacks.connect
		self.figure.canvas.mpl_connect('button_release_event', self.mouseUp)  
		
		self.setAcceptDrops(True)
		self.dropped=drop()
		
# right click context menu
	def contextMenuEvent(self, event):
	
		try:
			menu = QtWidgets.QMenu(self)
			copyAll = menu.addAction("Copy Data,fit,residual and distribution")
			copyDistribution = menu.addAction("Copy Distribution")
			action = menu.exec_(self.mapToGlobal(event.pos()))
			if action == copyAll:
				self.toClipboardAll()
#				self.toClipboardCurrent()
			if action == copyDistribution:
				if check:
					self.toClipboardDistribution()
		except:
			pass


	def toClipboardAll(self):
		global data, fit, distribution,lt,ut,index,check,checkBox,fileDialog,trace,dual, stau
	# Create string from array
		line_strings = []
		if check:
			maxlen=max(len(data[0]),len(distribution[index-1][2][:]))
		else:
			maxlen=len(data[0])
		#self.array=zeros(maxlen)
		line_strings.append(unicode(fileDialog[fileDialog.rfind(u'/')+1:]))

		if checkBox.isChecked():
			if check:
				line_strings.append("alpha= %0.4e" %float(alpha[index-1]))

				line_strings.append("tau	FCF	tau	fit	residual	distribution")
				self.array=vstack((append(data[0],zeros(abs(maxlen-len(data[0])))), \
				append(data[2],zeros(abs(maxlen-len(data[2])))),\
				append(distribution[index-1][2][:],zeros(abs(maxlen-len(distribution[index-1][2][:])))),\
				append(fit[index-1][0][:],zeros(abs(maxlen-len(fit[index-1][0][:])))),\
				append(residual[index-1][1][:],zeros(abs(maxlen-len(residual[index-1][1][:])))),\
				append(distribution[index-1][0][:],zeros(abs(maxlen-len(distribution[index-1][0][:]))))    ))
			else:
				line_strings.append("tau	FCF")
				self.array=vstack((data[0],data[2]))

		else:
			if check:
				line_strings.append("alpha= %0.4e" %float(alpha[index-1]))
				line_strings.append("tau	ICF	tau	fit	residual	distribution")
				self.array=vstack((append(data[0],zeros(abs(maxlen-len(data[0])))), \
				append(data[1],zeros(abs(maxlen-len(data[1])))),\
				append(distribution[index-1][2][:],zeros(abs(maxlen-len(distribution[index-1][2][:])))),\
				append(fit[index-1][0][:],zeros(abs(maxlen-len(fit[index-1][0][:])))),\
				append(residual[index-1][1][:],zeros(abs(maxlen-len(residual[index-1][1][:])))),\
				append(distribution[index-1][0][:],zeros(abs(maxlen-len(distribution[index-1][0][:]))))    ))
			else:
				line_strings.append("tau	ICF")
				self.array=vstack((data[0],data[1]))			
			
		for line in self.array.transpose():
			line_strings.append("\t".join(line.astype(str)).replace("\n",""))
		array_string = "\r\n".join(line_strings)

	# Put string into clipboard (open, clear, set, close)
		clipboard.OpenClipboard()
		clipboard.EmptyClipboard()
		clipboard.SetClipboardText(array_string)
		clipboard.CloseClipboard()
			
			
	def toClipboardDistribution(self):
		global data, fit, distribution,lt,ut,index,check,checkBox,fileDialog,trace,dual, stau
	# Create string from array
		line_strings = []
		line_strings.append(unicode(fileDialog[fileDialog.rfind(u'/')+1:]))
		line_strings.append("alpha= %0.4e" %float(alpha[index-1]))
		line_strings.append("tau	distribution")
		self.array=vstack((distribution[index-1][2][:],distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:]))))	
		
		for line in self.array.transpose():
			line_strings.append("\t".join(line.astype(str)).replace("\n",""))
		array_string = "\r\n".join(line_strings)

	# Put string into clipboard (open, clear, set, close)
		clipboard.OpenClipboard()
		clipboard.EmptyClipboard()
		clipboard.SetClipboardText(array_string)
		clipboard.CloseClipboard()
	
	# to selectthe boundary lines
	def mouseDown(self, evt):
		try:
			if self.linelt == evt.artist:
				self.state = 'lt'
		
			elif self.lineut == evt.artist:
				self.state = 'ut'
				
			else:
				self.state = ''
		except:
			pass
		
			# when releasing the boundary line, to updat its position
	def mouseUp(self, evt):
		global lt, ut

		if self.state == '':
			return			
			
		x= data[0][npabs(data[0]-evt.xdata).argmin():npabs(data[0]-evt.xdata).argmin()+1]   #originally=evt.xdata
		if x is None:  # outside the axes
			return

		if self.state == 'lt':
			self.lt.set(x)
			lt=x
			self.changeit()			
		elif self.state == 'ut':
			self.ut.set(x)
			ut=x
			self.changeit()
		self.state = ''
		
				
 # the following 2 functions serve for the drag and drop of files
	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			links = []
			for url in event.mimeData().urls():
				# print(unicode(url.toLocalFile()))
				# print(str(url.toLocalFile()).decode("utf-8"))
				links.append(unicode(url.toLocalFile()))
			# self.dropped=QtCore.Signal(str)
			# dropped.connect(self.fileDropped)
			self.dropped.ds.emit(links)
		else:
			event.ignore()

			
			# this updates the graphs
	def changeit(self):
		global data, fit, distribution,lt,ut,index,check,checkBox,fileDialog,trace,dual, stau
	
		if dual:
			if checkBox.isChecked():

				if check: 
					self.a2.set_ydata(data[2])
					self.a4.set_ydata(data[5])
					self.a3.set_ydata(distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:])))				
					self.a1.set_ydata(fit[index-1][0][:])						
					self.a5.set_ydata(residual[index-1][1][:])
					
					self.a2.set_xdata(data[0])
					self.a4.set_xdata(data[3])
					self.a3.set_xdata(distribution[index-1][2][:])				
					self.a1.set_xdata(fit[index-1][1][:])						
					self.a5.set_xdata(residual[index-1][0][:])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)			
				
				else:
					self.a2.set_ydata(data[2])
					self.a4.set_ydata(data[5])
					self.a2.set_xdata(data[0])
					self.a4.set_xdata(data[3])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)	
			else:
				if check: 
					self.a2.set_ydata(data[1])
					self.a4.set_ydata(data[4])
					self.a3.set_ydata(distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:])))				
					self.a1.set_ydata(fit[index-1][0][:])						
					self.a5.set_ydata(residual[index-1][1][:])
					
					self.a2.set_xdata(data[0])
					self.a4.set_xdata(data[3])
					self.a3.set_xdata(distribution[index-1][2][:])				
					self.a1.set_xdata(fit[index-1][1][:])						
					self.a5.set_xdata(residual[index-1][0][:])
					
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)			
				
				else:
					self.a2.set_ydata(data[1])
					self.a4.set_ydata(data[4])
					self.a2.set_xdata(data[0])
					self.a4.set_xdata(data[3])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)		
		else:
			if checkBox.isChecked():

				if check: 
					self.a2.set_ydata(data[2])
					self.a3.set_ydata(distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:])))				
					self.a1.set_ydata(fit[index-1][0][:])						
					self.a5.set_ydata(residual[index-1][1][:])
					
					self.a2.set_xdata(data[0])
					self.a3.set_xdata(distribution[index-1][2][:])			
					self.a1.set_xdata(fit[index-1][1][:])						
					self.a5.set_xdata(residual[index-1][0][:])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)			
				
				else:
					self.a2.set_ydata(data[2])
					self.a2.set_xdata(data[0])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)	
			else:
				if check: 
					self.a2.set_ydata(data[1])
					self.a3.set_ydata(distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:])))				
					self.a1.set_ydata(fit[index-1][0][:])						
					self.a5.set_ydata(residual[index-1][1][:])
					
					self.a2.set_xdata(data[0])
					self.a3.set_xdata(distribution[index-1][2][:])			
					self.a1.set_xdata(fit[index-1][1][:])						
					self.a5.set_xdata(residual[index-1][0][:])
					
					
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)			
				
				else:
					self.a2.set_ydata(data[1])
					self.a2.set_xdata(data[0])
					self.linelt.set_xdata(self.lt.value)
					self.lineut.set_xdata(self.ut.value)				
				
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()  			

	
   # draws the graphs, after loading the data
	def drawit(self):	
		global data, fit, distribution,lt,ut,index,check,checkBox,fileDialog,trace,dual, stau
		filename=fileDialog		  
		self.figure.clear()

		gs=gridspec.GridSpec(4,1)  
		lt=self.lt.value
		ut=self.ut.value
		self.axes1 = self.figure.add_subplot(gs[1:,:])	
		if stau:
			self.axes1.set_xlabel(r"$\tau$", fontsize = 15)#, weight='bold')
		else:
			self.axes1.set_xlabel(r"$\tau$ [s]", fontsize = 15)
		self.axes2 = self.figure.add_subplot(gs[0,:])	
		self.figure.tight_layout()
		if dual:
			self.axes2.plot(trace[0],trace[1],color='k')
			self.axes2.plot(trace[2],trace[3],color='purple',)
		elif threeD:
			self.axes2.plot(trace[0],trace[1],color='k')
			self.axes2.plot(trace[0],trace[2],color='purple',)			
		
		else:
			self.axes2.plot(trace[0],trace[1],color='k')
					
		self.max_yticks = 3
		self.yloc =MaxNLocator(self.max_yticks)
		self.axes2.yaxis.set_major_locator(self.yloc)
		self.axes2.set_ylabel(r"I", fontsize = 15) 
		if dual:
			if checkBox.isChecked():
				if check: 
					self.a2, =self.axes1.plot(data[0], data[2],color='k', linewidth=1,label='FCF',marker="s", fillstyle='none',markersize=5)
					self.a4, =self.axes1.plot(data[3], data[5],color='purple', linewidth=1,label='2nd channel',marker="s", fillstyle='none',markersize=5)
 				
					self.a3, =self.axes1.semilogx(distribution[index-1][2][:], (distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:]))), marker="o",markersize=5,color=(0,0.666,0),\
					linewidth=1,label='Contin distribution(Rescaled)')			
					self.a1, =self.axes1.semilogx(fit[index-1][1][:], fit[index-1][0][:],color=(1,0,0), linewidth=1.5,label='Contin fit') #self.lines1 += 	
					self.a5, =self.axes1.semilogx(residual[index-1][0][:], residual[index-1][1][:],color=(0,0,1), linewidth=1.5,label='Residuals')
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--', linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5) # replaced utfor self.ut.value	
					h2,h1=self.axes1.get_legend_handles_labels()		
				
				else:	   
					self.a2, =self.axes1.semilogx(data[0], data[2],color='k', fillstyle='none',linewidth=1,label='FCF',marker="s",markersize=5) 
					self.a4, =self.axes1.plot(data[3], data[5],color='purple', linewidth=1,label='2nd channel',marker="s", fillstyle='none',markersize=5)
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--',linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)		
			else:		
				if check: 
		#			self.M=fit[index-1][0][:].max()/distribution[index-1][0][:].max()
					self.a2, =self.axes1.semilogx(data[0], data[1],color='k',fillstyle='none', linewidth=1,label='ICF',marker="s",markersize=5)
					self.a4, =self.axes1.plot(data[3], data[4],color='purple', linewidth=1,label='2nd channel',marker="s", fillstyle='none',markersize=5)				
					self.a3, =self.axes1.semilogx(distribution[index-1][2][:], (distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:]))), marker="o",markersize=5,color=(0,0.666,0),\
					linewidth=1,label='Contin distribution(Rescaled)')
					self.a1, =self.axes1.semilogx(fit[index-1][1][:], fit[index-1][0][:],color=(1,0,0), linewidth=1.5,label='Contin fit')
					self.a5, =self.axes1.semilogx(residual[index-1][0][:], residual[index-1][1][:],color=(0,0,1), linewidth=1.5,label='Residuals')
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--', linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)	
				
				else:	   
					self.a2, =self.axes1.semilogx(data[0], data[1],color='k', linewidth=1,fillstyle='none',label='ICF',marker="s",markersize=5) 
					self.a4, =self.axes1.plot(data[3], data[4],color='purple', linewidth=1,label='2nd channel',marker="s", fillstyle='none',markersize=5)
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--',linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)		
		else:		
			if checkBox.isChecked():
				if check: 
					self.a2, =self.axes1.plot(data[0], data[2],color='k', linewidth=1,label='FCF',marker="s", fillstyle='none',markersize=5)		
					self.a3, =self.axes1.semilogx(distribution[index-1][2][:], (distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:]))), marker="o",markersize=5,color=(0,0.666,0),\
					linewidth=1,label='Contin distribution(Rescaled)')		
					self.a1, =self.axes1.semilogx(fit[index-1][1][:], fit[index-1][0][:],color=(1,0,0), linewidth=1.5,label='Contin fit') #self.lines1 += 	
					self.a5, =self.axes1.semilogx(residual[index-1][0][:], residual[index-1][1][:],color=(0,0,1), linewidth=1.5,label='Residuals')

					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--', linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)	
					h2,h1=self.axes1.get_legend_handles_labels()		
				
				else:	   
					self.a2, =self.axes1.semilogx(data[0], data[2],color='k', fillstyle='none',linewidth=1,label='FCF',marker="s",markersize=5)
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--',linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)		
			else:		
				if check: 
					self.a2, =self.axes1.semilogx(data[0], data[1],color='k',fillstyle='none', linewidth=1,label='ICF',marker="s",markersize=5)				
					self.a3, =self.axes1.semilogx(distribution[index-1][2][:], (distribution[index-1][0][:]*amax(fit[index-1][0][:]/amax(distribution[index-1][0][:]))), marker="o",markersize=5,color=(0,0.666,0),\
					linewidth=1,label='Contin distribution(Rescaled)')
					self.a1, =self.axes1.semilogx(fit[index-1][1][:], fit[index-1][0][:],color=(1,0,0), linewidth=1.5,label='Contin fit')
					self.a5, =self.axes1.semilogx(residual[index-1][0][:], residual[index-1][1][:],color=(0,0,1), linewidth=1.5,label='Residuals')

					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--', linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)	
			
				else:	   
					self.a2, =self.axes1.semilogx(data[0], data[1],color='k', linewidth=1,fillstyle='none',label='ICF',marker="s",markersize=5) 
					self.linelt=self.axes1.axvline(self.lt.value, linestyle='--',linewidth=1, color='k', picker=5)
					self.lineut=self.axes1.axvline(self.ut.value, linestyle='--', linewidth=1, color='k', picker=5)
		self.axes1.legend(loc='upper right', shadow=False,frameon=False, fontsize=12)
	
		self.figure.canvas.draw()
		self.figure.canvas.flush_events() 
		
		
		
		
class Ui_Continizer(object):
	def setupUi(self, Continizer):
		global checkBox,x,y,fileDialog
		self.filename = ""
		Continizer.setObjectName(("Continizer"))
		Continizer.resize(732, 613)
		self.centralwidget = QtWidgets.QWidget(Continizer)
		self.centralwidget.setObjectName(("centralwidget"))
		self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
		self.gridLayout.setObjectName(("gridLayout"))
		self.verticalLayout = QtWidgets.QVBoxLayout()
		self.verticalLayout.setObjectName(("verticalLayout"))
		self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
		self.horizontalLayout_3.setObjectName(("horizontalLayout_3"))
		self.pushopen = QtWidgets.QPushButton(self.centralwidget)
		self.pushopen.setObjectName(("pushopen"))
		self.horizontalLayout_3.addWidget(self.pushopen)
		spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout_3.addItem(spacerItem3)

		self.pushcontin = QtWidgets.QPushButton(self.centralwidget)
		self.pushcontin.setObjectName(("pushcontin"))
		self.horizontalLayout_3.addWidget(self.pushcontin)
		self.verticalLayout.addLayout(self.horizontalLayout_3)
		self.graph = MatplotlibWidget(self.centralwidget)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(1)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.graph.sizePolicy().hasHeightForWidth())
		self.graph.setSizePolicy(sizePolicy)
		self.graph.setObjectName(("graphs"))
		self.verticalLayout.addWidget(self.graph)		
		self.toolbar = NavigationToolbar(self.graph, self.centralwidget)
		self.verticalLayout.addWidget(self.toolbar)
		self.horizontalLayout = QtWidgets.QHBoxLayout()
		self.horizontalLayout.setObjectName(("horizontalLayout"))
		self.label_1 = QtWidgets.QLabel(self.centralwidget)
		self.label_1.setObjectName(("label_1"))
		self.horizontalLayout.addWidget(self.label_1)
		self.spinBox = QtWidgets.QSpinBox(self.centralwidget)
		self.spinBox.setMinimum(1)
		self.spinBox.setMaximum(1)
		self.spinBox.setObjectName(("spinBox"))
		self.horizontalLayout.addWidget(self.spinBox)
		self.label_2 = QtWidgets.QLabel(self.centralwidget)
		self.label_2.setObjectName(("label_2"))
		self.horizontalLayout.addWidget(self.label_2)
		self.linealpha = QtWidgets.QLineEdit(self.centralwidget)
		self.linealpha.setObjectName(("linealpha"))
		self.horizontalLayout.addWidget(self.linealpha)
		spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout.addItem(spacerItem1)
		checkBox = QtWidgets.QCheckBox(self.centralwidget)
		checkBox.setObjectName(("checkBox"))
		self.horizontalLayout.addWidget(checkBox)
		spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout.addItem(spacerItem2)
 
		self.pushexport = QtWidgets.QPushButton(self.centralwidget)
		self.pushexport.setObjectName(("pushexport"))
		self.horizontalLayout.addWidget(self.pushexport)
		self.verticalLayout.addLayout(self.horizontalLayout)
		self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
		Continizer.setCentralWidget(self.centralwidget)
		self.retranslateUi(Continizer,"Continizer")
		
		self.graph.dropped.ds.connect(self.fileDropped)
		
		QtCore.QObject.connect(self.spinBox, QtCore.SIGNAL(("valueChanged(int)")), self.updatealpha)
		QtCore.QObject.connect(self.pushcontin, QtCore.SIGNAL(("clicked()")), self.spinBox.update)
		QtCore.QObject.connect(self.pushcontin, QtCore.SIGNAL(("clicked()")), self.callCONTIN)
		QtCore.QObject.connect(self.pushopen, QtCore.SIGNAL("clicked()"), self.OnOpen)
		QtCore.QObject.connect(self.pushexport, QtCore.SIGNAL("clicked()"), self.export)
		QtCore.QObject.connect(checkBox, QtCore.SIGNAL(("stateChanged(int)")), self.sqrt)
		QtCore.QMetaObject.connectSlotsByName(Continizer)

		self.spinBox.setToolTip(("Change to a different solution."))
		self.pushexport.setToolTip(("Export displayed data. (as Filename.czr)"))			
		self.pushopen.setToolTip(("Open a new dataset.")) 
		self.pushcontin.setToolTip(("Run contin with selected data range."))
		checkBox.setToolTip(("Applies square root. (Field correlation function)"))
		self.graph.figure.canvas.mpl_connect('motion_notify_event', self.Showtooltip)		#'motion_notify_event'
		
		# self.setAcceptDrops(True)
		
		
	def fileDropped(self, l):
		global fileDialog 
		for url in l:
			if path.exists(url):
				fileDialog=url
				self.open()				

 
	def Showtooltip(self, event):
		global x,y, index, counterfit, peak,fileDialog,Rhconv,trace,dual,theta1,theta2
		x, y = event.xdata, event.ydata

	   
		if event.inaxes:		 		
			if event.inaxes==self.graph.axes1:
				if lense: 
					if check:
						if peak[index-1][0][0]<=event.xdata<=peak[index-1][counterfit[index-1]-1][1]:
							i=0  
							while i < counterfit[index-1]:
 #					   print (peak[index-1][i][0])
								self.I=i+1		
								if peak[index-1][i][0]<=event.xdata<=peak[index-1][i][1]:
									self.graph.setToolTip("PEAK %d\nAverage time = %0.4e +- %0.1e %% \nAmplitude = %0.4e +- %0.1e %%\n\
Rh(assuming field correlation function\nand using theta1= %0.2e,theta2= %0.2e)=%0.2e nm\nx=%0.2e y=%f"\
									%(self.I,((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),(math.sqrt(((2*(peak[index-1][i][4])*(peak[index-1][i][5]*\
peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))*((2*(peak[index-1][i][4])*\
(peak[index-1][i][5]*peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))  +  ((1.5*(peak[index-1][i][4])*(peak[index-1][i][4])\
*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))*((1.5*(peak[index-1][i][4])*\
(peak[index-1][i][4])*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*\
(peak[index-1][i][2])))*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))	+  \
  ((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]\
  /peak[index-1][i][6]))*((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))))/((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),\
									peak[index-1][i][2],peak[index-1][i][3],theta1,theta2,x*Rhconv,x,y))									
		#'PEAK Num. %d\nx=%0.10f y=%f'%(self.I,x,y))
									break							
								i+=1 				
					
						else:
							self.graph.setToolTip('Rh(assuming field correlation function\nand using theta1= %0.2e,theta2= %0.2e)=%0.2e nm\nx=%0.2e y=%f'%(theta1,theta2,x*Rhconv,x,y))	   

					else:
						self.graph.setToolTip('Rh(assuming field correlation function\nand using theta1= %0.2e,theta2= %0.2e)=%0.2e nm\nx=%0.2e y=%f'%(theta1,theta2,x*Rhconv,x,y))
						
				else:
					if check:
						if peak[index-1][0][0]<=event.xdata<=peak[index-1][counterfit[index-1]-1][1]:
							i=0  
							while i < counterfit[index-1]:
 #					   print (peak[index-1][i][0])
								self.I=i+1		
								if peak[index-1][i][0]<=event.xdata<=peak[index-1][i][1]:
									self.graph.setToolTip("PEAK %d\nAverage time = %0.4e +- %0.1e %% \nAmplitude = %0.4e +- %01.e %%\n\
Rh(assuming field correlation function)=%0.2e nm\nx=%0.2e y=%f"\
									%(self.I,((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),(math.sqrt(((2*(peak[index-1][i][4])*(peak[index-1][i][5]*\
peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))*((2*(peak[index-1][i][4])*\
(peak[index-1][i][5]*peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))  +  ((1.5*(peak[index-1][i][4])*(peak[index-1][i][4])\
*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))*((1.5*(peak[index-1][i][4])*\
(peak[index-1][i][4])*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*\
(peak[index-1][i][2])))*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))	+  \
  ((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]\
  /peak[index-1][i][6]))*((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))))/((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),\
									peak[index-1][i][2],peak[index-1][i][3],x*Rhconv,x,y))
#				(m0/m-1)^2 *sqrt(m-1/m1)   num=4,2,2,6			
		#'PEAK Num. %d\nx=%0.10f y=%f'%(self.I,x,y))
									break							
								i+=1
								
 		
						else:
							self.graph.setToolTip('Rh(assuming field correlation function)=%0.2e nm\nx=%0.2e y=%f'%(x*Rhconv,x,y))	   

					else:
						self.graph.setToolTip('Rh(assuming field correlation function)=%0.2e nm\nx=%0.2e y=%f'%(x*Rhconv,x,y))

				
				
				
			elif event.inaxes==self.graph.axes2:
				if dual:			
					self.graph.setToolTip('Time=%d Counts=%0.3f'%(x,y))
				else:			
					self.graph.setToolTip('Time=%d Counts=%0.3f'%(x,trace[1][npabs(x-trace[0]).argmin()]))
		   #	 self.graph.axes2.plot(x,y, 'ro')
			#	self.graph.axes2.show()
#peak[-1][-1]=[rangea,rangeb,m-1,e-1,m0,e0,m1,e1,m2,e2,std/mean,m3,e3]
			
		
#simple siegert sqrt function , comment this and uncomment the following to use the complete equation		
	def sqrt(self):  
		global check,lt,ut,data,slt,sut,fstar,dual

		a=open('FSTAR.IN','r')
		b=a.read()
		a.close()
		fstar=float(b)		
		self.sut=data[1]/fstar#*np.ones(data[1].size)
		data[2]=(npabs(self.sut))**0.5*sign(self.sut)
		if dual:

			self.sut=data[4]/fstar#*np.ones(data[1].size)
			data[5]=(npabs(self.sut))**0.5*sign(self.sut)		
	
		if check:
			self.graph.drawit()
			self.callCONTIN()	
	
		elif self.graph:
			self.graph.drawit()	
	
#	def sqrt(self):
#		global check,lt,ut,data,slt,sut,fstar,dual

#	#	a=open('FSTAR.IN','r')
#	#	b=a.read()
#	#	a.close()
#	#	fstar=float(b)#	#	
#	#	slt=mean(data[1][npabs(data[0]-lt).argmin()-2:npabs(data[0]-lt).argmin()+2]/fstar)
#	#	sut=mean(data[1][npabs(data[0]-ut).argmin()-2:npabs(data[0]-ut).argmin()+2]/fstar)
#	#	self.B=(1-slt+sut)**0.5  #ones(data[1].size)
#	#	self.sut=data[1]/fstar-sut  #*np.ones(data[1].size)
#	#	data[2]=(-self.B+((self.B**2)+(self.sut))**0.5)/(1-self.B)#
#	#	if dual:
#	#	#	slt=mean(data[4][npabs(data[3]-lt).argmin()-2:npabs(data[3]-lt).argmin()+2]/fstar)
#	#	#	sut=data[1][abs(data[0]-ut).argmin()]
#	#	#	sut=mean(data[4][npabs(data[3]-ut).argmin()-2:npabs(data[3]-ut).argmin()+2]/fstar)
#	#	#	self.B=(1-slt+sut)**0.5#ones(data[1].size)*
#	#	#	self.sut=data[4]/fstar-sut#*np.ones(data[1].size)
#	#	    data[5]=(-self.B+((self.B**2)+(self.sut))**0.5)/(1-self.B)#  #		
	
#	#	if check:
#	#	#	self.callCONTIN()#		
#	#	elif self.graph:
#			self.graph.drawit()	

		
	def updatealpha(self,ind):
		global alpha, index
		index=ind
		self.linealpha.setText(unicode(alpha[index-1]))
		self.graph.changeit()
	   

	def retranslateUi(self, Continizer,title):
		global checkBox
		Continizer.setWindowTitle(title)
		self.pushopen.setText( "Open Correlogram")
		self.pushcontin.setText("Run Contin")
		self.label_1.setText( "Solution")
		self.label_2.setText( "Alpha")
		self.pushexport.setText( "Export")
		checkBox.setText( "Siegert Relationship")
		
	def OnOpen(self):
		global check, alpha, fileDialog,dir,dual,lense,stau,threeD
		path = QtWidgets.QFileInfo(self.filename).path() \
		if not self.filename=="" else "."
   #	 if not dir:
		fileDialog,_ = QtWidgets.QFileDialog.getOpenFileName(None,
							"Continizer - Open",
							filter="ALV ASCII (*.ASC);;ALV BINARY (*.DAT);;CORRELATOR.COM (*.SIN);;CORRELATOR.COM (*.COQ);;UNFORMATTED")		
		# fileDialog = str(fileDialog).decode("utf-8")
		fileDialog = unicode(fileDialog)
		if fileDialog != '':self.open()
							
	def open(self):
		global check, alpha, fileDialog,dir,dual,lense,stau,threeD
		dual=False	
		lense=False	
		stau=False	
		threeD=False	
		# try:
		if fileDialog[-3:]=='ASC': 
			self.getfileASC(fileDialog)
			check=False
		elif fileDialog[-3:]=='asc': 
			self.getfileASC(fileDialog)
			check=False
		elif fileDialog[-3:]=='DAT': 
			self.getfileBINand3D(fileDialog)
			check=False	
		elif fileDialog[-3:]=='dat': 
			self.getfileBINand3D(fileDialog)
			check=False						
		elif fileDialog[-3:]=='SIN':
			self.getfileCOM(fileDialog)
			check=False
		elif fileDialog[-3:]=='sin': 
			self.getfileCOM(fileDialog)
			check=False
		elif fileDialog[-3:]=='COQ': 
			self.getfileCOM(fileDialog)
			check=False
		elif fileDialog[-3:]=='coq':
			self.getfileCOM(fileDialog)
			check=False
		else:
			self.getfileCSV(fileDialog)
			check=False
			stau=True
		self.retranslateUi(Continizer, "Continizer - "+fileDialog)			
		alpha=[]
		self.graph.lt.set(data[0][0]*10)
		self.graph.ut.set(data[0][-1]/10)
		self.linealpha.setText('')
		self.spinBox.setMaximum(1)
		self.sqrt()



	def getfileBINand3D(self, path=None):
		global data,Rhconv,trace,dual,lense,theta1,theta2,threeD
		if path is None:
			self.data=array([[0.1,2,300],[1,1,100]])
		else:
			a=open(path,'r')
			b=a.read()
			a.close()

			if 'Laser intensity (mW):' in b:

				threeD=True  
				self.T=genfromtxt(StringIO(b[b.find('Temperature (K):')+b[b.find('Temperature (K):'):].find('	'):b.find('Temperature (K):')+b[b.find('Temperature (K):'):].find('\n')]))            
				self.eta=genfromtxt(StringIO(b[b.find('Viscosity (mPas):')+b[b.find('Viscosity (mPas):'):].find('	'):b.find('Viscosity (mPas):')+b[b.find('Viscosity (mPas):'):].find('\n')]))            
				self.n=genfromtxt(StringIO(b[b.find('Refractive index:')+b[b.find('Refractive index:'):].find('	'):b.find('Refractive index:')+b[b.find('Refractive index:'):].find('\n')]))            
				self.l=genfromtxt(StringIO(b[b.find('Wavelength (nm):')+b[b.find('Wavelength (nm):'):].find('	'):b.find('Wavelength (nm):')+b[b.find('Wavelength (nm):'):].find('\n')]))            
				self.theta=genfromtxt(StringIO(b[b.find('Scattering angle:')+b[b.find('Scattering angle:'):].find('	'):b.find('Scattering angle:')+b[b.find('Scattering angle:'):].find('\n')]) )        

				Rhconv=10**27*(1.38E-23)*self.T*4**2*math.pi**2*self.n**2*(math.sin(self.theta*math.pi/360))**2/(6*math.pi*(self.eta/1000)*self.l**2)
				begin=b.find('g2-1')+b[b.find('g2-1'):].find('\n')
				end=b.find('g2-1')+b[b.find('g2-1'):].find('NaN')-3
				substring = b[begin:end]
				substring = substring[:substring.rfind("\n")]
				d=genfromtxt(StringIO(substring))
				self.data=transpose(d)								
				data=vstack((vstack((self.data[0][5:],self.data[1][5:])),self.data[1][5:]))#

				f=genfromtxt(StringIO(b[b.find('History')+b[b.find('History'):].find('\n'):]))
				trace=transpose(f)
			

				self.graph.drawit()

				
			else:
				a=open(path,'rb')
				b=a.read()
				a.close()

				self.T=unpack('d',b[b.find("TEMP")+4+4:b.find("TEMP")+4+4+8])[0]
				theta2=unpack('d',b[b.find("ANG ")+4+4:b.find("ANG ")+4+4+8])[0] 
				self.n=unpack('d',b[b.find("IND")+4+4:b.find("IND")+4+4+8])[0] 		   
				self.eta=unpack('d',b[b.find("VISC")+4+4:b.find("VISC")+4+4+8])[0]		   
				self.l=unpack('d',b[b.find("WAVE")+4+4:b.find("WAVE")+4+4+8])[0]  			
				Rhconv=10**27*(1.38E-23)*self.T*4**2*math.pi**2*self.n**2*(math.sin(theta2*math.pi/360))**2/(6*math.pi*(self.eta/1000)*self.l**2)
				if 'theta1=' in b:
					self.t1=unpack('2h',b[b.find('SMPL')+4:b.find('SMPL')+4+4])[0]
					theta1=float(b[b.find('=')+1:b.find('SMPL')+4+4+self.t1])
					self.thetas=theta2-(90-theta1)				
					Rhconv=10**27*(1.38E-23)*self.T*4**2*math.pi**2*self.n**2*(math.sin(math.acos(1.62/self.n*math.cos(self.thetas*math.pi/180))/2))**2/(6*math.pi*(self.eta/1000)*self.l**2)
					lense=True
				self.dur=unpack('d',b[b.find("DUR")+3+4:b.find("DUR")+3+4+8])[0]

				self.mode=unpack('h',b[b.find("MODE")+4+4:b.find("MODE")+4+4+2])[0] 		
				self.points0=unpack('2h',b[b.find("COR0")+4:b.find("COR0")+4+4])[0] 
				self.y=array(unpack('%df'%(self.points0),b[b.find("COR0")+4+4:b.find("COR0")+4+4+self.points0*4]))
			
				if 'COR1' in b:			
					self.points1=unpack('2h',b[b.find("COR1")+4:b.find("COR1")+4+4])[0]
					self.y1=array(unpack('%df'%(self.points1),b[b.find("COR1")+4+4:b.find("COR1")+4+4+self.points1*4]))
					dual=True
				
				if self.mode==12:
					self.x=array([0,1.25E-08,0.000000025,3.75E-08,0.00000005,6.25E-08,0.000000075,8.75E-08,0.0000001,1.125E-07,0.000000125,1.375E-07,0.00000015,1.625E-07,0.000000175,1.875E-07,0.0000002,0.000000225,0.00000025,0.000000275,0.0000003,0.000000325,0.00000035,0.000000375,0.0000004,0.00000045,0.0000005,0.00000055,0.0000006,0.00000065,0.0000007,0.00000075,0.0000008,0.0000009,0.000001,0.0000011,0.0000012,0.0000013,0.0000014,0.0000015,0.0000016,0.0000018,0.000002,0.0000022,0.0000024,0.0000026,0.0000028,0.000003,0.0000032,0.0000036,0.000004,0.0000044,0.0000048,0.0000052,0.0000056,0.000006,0.0000064,0.0000072,0.000008,0.0000088,0.0000096,0.0000104,0.0000112,0.000012,0.0000128,0.0000144,0.000016,0.0000176,0.0000192,0.0000208,0.0000224,0.000024,0.0000256,0.0000288,0.000032,0.0000352,0.0000384,0.0000416,0.0000448,0.000048,0.0000512,0.0000576,0.000064,0.0000704,0.0000768,0.0000832,0.0000896,0.000096,0.0001024,0.0001152,0.000128,0.0001408,0.0001536,0.0001664,0.0001792,0.000192,0.0002048,0.0002304,0.000256,0.0002816,0.0003072,0.0003328,0.0003584,0.000384,0.0004096,0.0004608,0.000512,0.0005632,0.0006144,0.0006656,0.0007168,0.000768,0.0008192,0.0009216,0.001024,0.0011264,0.0012288,0.0013312,0.0014336,0.001536,0.0016384,0.0018432,0.002048,0.0022528,0.0024576,0.0026624,0.0028672,0.003072,0.0032768,0.0036864,0.004096,0.0045056,0.0049152,0.0053248,0.0057344,0.006144,0.0065536,0.0073728,0.008192,0.0090112,0.0098304,0.0106496,0.0114688,0.012288,0.0131072,0.0147456,0.016384,0.0180224,0.0196608,0.0212992,0.0229376,0.024576,0.0262144,0.0294912,0.032768,0.0360448,0.0393216,0.0425984,0.0458752,0.049152,0.0528384,0.059392,0.0659456,0.0724992,0.0790528,0.0856064,0.09216,0.0987136,0.105267,0.118374,0.131482,0.144589,0.157696,0.170803,0.18391,0.197018,0.210125,0.236339,0.262554,0.288768,0.314982,0.341197,0.367411,0.393626,0.41984,0.472269,0.524698,0.577126,0.629555,0.681984,0.734413,0.786842,0.83927,0.944128,1.04899,1.15384,1.2587,1.36356,1.46842,1.57327,1.67813,1.88785,2.09756,2.30728,2.51699,2.72671,2.93642,3.14614,3.35585,3.77528,4.19471,4.61414,5.03357,5.453,5.87244,6.29187,6.7113,7.55016,8.38902,9.22788,10.0667,10.9056,11.7445,12.5833,13.4222,15.0999,16.7776,18.4553,20.1331,21.8108,23.4885,25.1662,26.844,30.1994,33.5548,36.9103,40.2657,43.6212,46.9766,50.3321,53.6875,60.3984,67.1093,73.8202,80.531,87.2419,93.9528,100.664,107.375,120.796,134.218,147.64,161.062,174.483,187.905,201.327,214.749,241.592,268.436,295.279,322.123,348.967,375.81,402.654,429.497,483.184,536.871,590.558,644.246,697.933,751.62,805.307,858.994,966.368,1073.74,1181.12,1288.49,1395.86,1503.24,1610.61,1717.99,1932.74,2147.48,2362.23,2576.98,2791.73,3006.48,3221.23])
					data=vstack((vstack((self.x[4:self.points0],self.y[4:]-1)),npabs(self.y[4:]-1)**0.5))#4
				elif self.mode==0:
					self.x=array([0,0.0000004,.0000008,.0000012,.0000016,.000002,.0000024,.0000028,.0000032,.0000036,.000004,.0000044,.0000048,.0000052,.0000056,.000006,.0000064,.0000072,.000008,.0000088,.0000096,.0000104,.0000112,.000012,.0000128,.0000144,.000016,.0000176,.0000192,.0000208,.0000224,.000024,.0000256,.0000288,.000032,.0000352,.0000384,.0000416,.0000448,.000048,.0000512,.0000576,.000064,.0000704,.0000768,.0000832,.0000896,.000096,.0001024,.0001152,.000128,.0001408,.0001536,.0001664,.0001792,.000192,.0002048,.0002304,.000256,.0002816,.0003072,.0003328,.0003584,.000384,.0004096,.0004608,.000512,.0005632,.0006144,.0006656,.0007168,.000768,.0008192,.0009216,.001024,.0011264,.0012288,.0013312,.0014336,.001536,.0016384,.0018432,.002048,.0022528,.0024576,.0026624,.0028672,.003072,.0032768,.0036864,.004096,.0045056,.0049152,.0053248,.0057344,.006144,.0065536,.0073728,.008192,.0090112,.0098304,.0106496,.0114688,.012288,.0131072,.0147456,.016384,.0180224,.0196608,.0212992,.0229376,.024576,.0262144,.0294912,.032768,.0360448,.0393216,.0425984,.0458752,.049152,.0524288,.0589824,.065536,.0720896,.0786432,.0851968,.0917504,.098304,.105677,.118784,.131891,.144998,.158106,.171213,.18432,.197427,.210534,.236749,.262963,.289178,.315392,.341606,.367821,.394035,.42025,.472678,.525107,.577536,.629965,.682394,.734822,.787251,.83968,.944538,1.0494,1.15425,1.25911,1.36397,1.46883,1.57368,1.67854,1.88826,2.09797,2.30769,2.5174,2.72712,2.93683,3.14655,3.35626,3.77569,4.19512,4.61455,5.03398,5.45341,5.87284,6.29228,6.71171,7.55057,8.38943,9.22829,10.0671,10.906,11.7449,12.5837,13.4226,15.1003,16.778,18.4558,20.1335,21.8112,23.4889,25.1666,26.8444,30.1998,33.5553,36.9107,40.2661,43.6216,46.977,50.3325,53.6879,60.3988,67.1097,73.8206,80.5315,87.2423,93.9532,100.664,107.375,120.797,134.219,147.64,161.062,174.484,187.906,201.327,214.749,241.593,268.436,295.28,322.123,348.967,375.81,402.654,429.498,483.185,536.872,590.559,644.246,697.933,751.62,805.307,858.994,966.368,1073.74,1181.12,1288.49,1395.87,1503.24,1610.61,1717.99,1932.74,2147.48,2362.23,2576.98,2791.73,3006.48,3221.23,3435.97,3865.47,4294.97,4724.46,5153.96,5583.46,6012.96,6442.45])
					data=vstack((vstack((self.x[4:self.points0],self.y[4:]-1)),npabs(self.y[4:]-1)**0.5))#1
					if 'COR1'in b:				
					   data=vstack((data,vstack((self.x[4:self.points1],self.y1[4:]-1)),npabs(self.y1[4:]-1)**0.5))
				elif self.mode==4:
					self.x=array([0,0.0000002,0.0000004,0.0000006,0.0000008,0.000001,0.0000012,0.0000014,0.0000016,0.0000018,0.000002,0.0000022,0.0000024,0.0000026,0.0000028,0.000003,0.0000032,0.0000036,0.000004,0.0000044,0.0000048,0.0000052,0.0000056,0.000006,0.0000064,0.0000072,0.000008,0.0000088,0.0000096,0.0000104,0.0000112,0.000012,0.0000128,0.0000144,0.000016,0.0000176,0.0000192,0.0000208,0.0000224,0.000024,0.0000256,0.0000288,0.000032,0.0000352,0.0000384,0.0000416,0.0000448,0.000048,0.0000512,0.0000576,0.000064,0.0000704,0.0000768,0.0000832,0.0000896,0.000096,0.0001024,0.0001152,0.000128,0.0001408,0.0001536,0.0001664,0.0001792,0.000192,0.0002048,0.0002304,0.000256,0.0002816,0.0003072,0.0003328,0.0003584,0.000384,0.0004096,0.0004608,0.000512,0.0005632,0.0006144,0.0006656,0.0007168,0.000768,0.0008192,0.0009216,0.001024,0.0011264,0.0012288,0.0013312,0.0014336,0.001536,0.0016384,0.0018432,0.002048,0.0022528,0.0024576,0.0026624,0.0028672,0.003072,0.0032768,0.0036864,0.004096,0.0045056,0.0049152,0.0053248,0.0057344,0.006144,0.0065536,0.0073728,0.008192,0.0090112,0.0098304,0.0106496,0.0114688,0.012288,0.0131072,0.0147456,0.016384,0.0180224,0.0196608,0.0212992,0.0229376,0.024576,0.0262144,0.0294912,0.032768,0.0360448,0.0393216,0.0425984,0.0458752,0.049152,0.0528384,0.059392,0.0659456,0.0724992,0.0790528,0.0856064,0.09216,0.0987136,0.105267,0.118374,0.131482,0.144589,0.157696,0.170803,0.18391,0.197018,0.210125,0.236339,0.262554,0.288768,0.314982,0.341197,0.367411,0.393626,0.41984,0.472269,0.524698,0.577126,0.629555,0.681984,0.734413,0.786842,0.83927,0.944128,1.04899,1.15384,1.2587,1.36356,1.46842,1.57327,1.67813,1.88785,2.09756,2.30728,2.51699,2.72671,2.93642,3.14614,3.35585,3.77528,4.19471,4.61414,5.03357,5.453,5.87244,6.29187,6.7113,7.55016,8.38902,9.22788,10.0667,10.9056,11.7445,12.5833,13.4222,15.0999,16.7776,18.4553,20.1331,21.8108,23.4885,25.1662,26.844,30.1994,33.5548,36.9103,40.2657,43.6212,46.9766,50.3321,53.6875,60.3984,67.1093,73.8202,80.531,87.2419,93.9528,100.664,107.375,120.796,134.218,147.64,161.062,174.483,187.905,201.327,214.749,241.592,268.436,295.279,322.123,348.967,375.81,402.654,429.497,483.184,536.871,590.558,644.246,697.933,751.62,805.307,858.994,966.368,1073.74,1181.12,1288.49,1395.86,1503.24,1610.61,1717.99,1932.74,2147.48,2362.23,2576.98,2791.73,3006.48,3221.23])
					data=vstack((vstack((self.x[4:self.points0],self.y[4:]-1)),npabs(self.y[4:]-1)**0.5))#1

				if 'TRA0' in b:
					self.trl=unpack('2h',b[b.find("TRA0")+4:b.find("TRA0")+4+4])[0]
					trace=vstack((arange(self.trl)*self.dur/self.trl,array(unpack('%df'%(self.trl),b[b.find("TRA0")+4+4:b.find("TRA0")+4+4+self.trl*4]))))					
				if 'TRA1' in b:
					self.trl=unpack('2h',b[b.find("TRA1")+4:b.find("TRA1")+4+4])[0]
					trace=vstack((trace,vstack((arange(self.trl)*self.dur/self.trl,array(unpack('%df'%(self.trl),b[b.find("TRA1")+4+4:b.find("TRA1")+4+4+self.trl*4]))))))					


				self.graph.drawit()	


	def getfileCOM(self, path=None):
		global data,Rhconv,trace
		if path is None:
			self.data=array([[0.1,2,300],[1,1,100]])
		else:
			a=open(path,'r')
			b=a.read()
			a.close()
			begin=b.find('[Corre')+b[b.find('[Corr'):].find('\n')
			end=b.find('[Corre')+b[b.find('[Corr'):].find('\n\n')
			
			d=genfromtxt(StringIO(b[begin:end]))#, dtype=str)
			self.data=transpose(d)			
	
			data=vstack((vstack((self.data[0],self.data[1]-1)),self.data[1]-1))
			if 'Temp' in b:	
				self.T=genfromtxt(StringIO(b[b.find('Temperature')+b[b.find('Temperature'):].find('='):b.find('Temperature')+b[b.find('Temperature'):].find('\n')]))[0]		   
				self.eta=genfromtxt(StringIO(b[b.find('Visc')+b[b.find('Visc'):].find('='):b.find('Visc')+b[b.find('Visc'):].find('\n')]))[0]			
				self.n=genfromtxt(StringIO(b[b.find('Index')+b[b.find('Index'):].find('='):b.find('Index')+b[b.find('Index'):].find('\n')]))[0]			
				self.l=genfromtxt(StringIO(b[b.find('Wave')+b[b.find('Wave'):].find('='):b.find('Wave')+b[b.find('Wave'):].find('\n')]))[0]			
				self.theta=genfromtxt(StringIO(b[b.find('Angle')+b[b.find('Angle'):].find('='):b.find('Angle')+b[b.find('Angle'):].find('\n')]) )[0]	   
				Rhconv=10**27*(1.38E-23)*self.T*4**2*math.pi**2*self.n**2*(math.sin(self.theta*math.pi/360))**2/(6*math.pi*(self.eta/1000)*self.l**2)
			else:
				Rhconv=1		

			f=genfromtxt(StringIO(b[b.find('TraceNumber')+b[b.find('TraceNumber'):].find('\n'):b.find('TraceNumber')+b[b.find('TraceNumber'):].find('[')]))
			g=transpose(f)			
			trace=vstack((g[0],g[1]))
	#		print trace
			self.graph.drawit()
			

	def getfileASC(self, path=None):
		global data,Rhconv,trace,slt,sut,dir
		
		if path is None:
			self.data=array([[0.1,2,300],[1,1,100]])

		else:				
			a=open(path,'r')
			b=a.read()
			a.close()  
			self.T=genfromtxt(StringIO(b[b.find('Temperature [K] :')+b[b.find('Temperature [K] :'):].find('   '):b.find('Temperature [K] :')+b[b.find('Temperature [K] :'):].find('\n')]))            
			self.eta=genfromtxt(StringIO(b[b.find('Viscosity [cp]  :')+b[b.find('Viscosity [cp]  :'):].find('   '):b.find('Viscosity [cp]  :')+b[b.find('Viscosity [cp]  :'):].find('\n')]))            
			self.n=genfromtxt(StringIO(b[b.find('Refractive Index:')+b[b.find('Refractive Index:'):].find('   '):b.find('Refractive Index:')+b[b.find('Refractive Index:'):].find('\n')]))            
			self.l=genfromtxt(StringIO(b[b.find('Wavelength [nm] :')+b[b.find('Wavelength [nm] :'):].find('   '):b.find('Wavelength [nm] :')+b[b.find('Wavelength [nm] :'):].find('\n')]))            
			self.theta=genfromtxt(StringIO(b[b.find('Angle ')+b[b.find('Angle '):].find('	     '):b.find('Angle ')+b[b.find('Angle '):].find('\n')]) )        

			Rhconv=10**27*(1.38E-23)*self.T*4**2*math.pi**2*self.n**2*(math.sin(self.theta*math.pi/360))**2/(6*math.pi*(self.eta/1000)*self.l**2)
 
			f=genfromtxt(StringIO(b[b.find('Count')+b[b.find('Count'):].find('\n'):]))
			trace=transpose(f)
 	 
	 
			if 'Lag' not in b:
				begin=b.find('Corre')+b[b.find('Corr'):].find('\n')
				end=b.find('Corre')+b[b.find('Corr'):].find('\n\n')
				d=genfromtxt(StringIO(b[begin:end]))
				self.data=transpose(d)								
				data=vstack((vstack((self.data[0]/1000,self.data[1])),self.data[1]))#
				self.graph.drawit()

			else:
				begin=b.find('[ms]')+b[b.find('[ms]'):].find('\n')
				end=b.find('[ms]')+b[b.find('[ms]'):].find('\n\n')
				d=genfromtxt(StringIO(b[begin:end]))
				self.data=transpose(d)
			
				data=vstack((vstack((self.data[0]/1000,self.data[1])),self.data[1]))#
				self.graph.drawit()	
 #		   dir=True
		 				
		
	def getfileCSV(self, path=None):
		global data,Rhconv,trace
		if path is None:
			self.data=array([[0.1,2,300],[1,1,100]])

		else:
			a=open(path,'r')
			b=a.read()
			a.close()
			d=genfromtxt(StringIO(b))
			self.data=transpose(d)
			data=vstack((self.data,npabs(self.data[1])**0.5))
			Rhconv=1
			trace=array([[],[]])
			self.graph.drawit()
		
	def inputdata (self):
		global lt, ut, data,checkBox,sut,slt
				
		return  data[0][npabs(data[0]-lt).argmin():npabs(data[0]-ut).argmin()+1],\
		data[1][npabs(data[0]-lt).argmin():npabs(data[0]-ut).argmin()+1],\
		data[2][npabs(data[0]-lt).argmin():npabs(data[0]-ut).argmin()+1]
		
		
	def makecontinIN (self):
		global lt,ut, checkBox,fileDialog
		file="contin.in"
		f=open(file,'w')
		filename=fileDialog
		p=open('PARAMETERS.IN','r')
		pp=p.read()
		p.close()
		
		inputx,inputy,inputysqrt=self.inputdata()
		
		print ( filename[filename.rfind('/')+1:],file=f)
		print ( pp%(lt,ut) ,file=f)		
		if len(inputx)<251:	  
			print ( u' NG                    %d.\n END\n NY      %d'%(len(inputx),len(inputx)),file=f)
			# print >> f, ' NG                    %d.\n END\n NY      %d'%(40,len(inputx))
		else:	  
			print( u' NG                    251.\n END\n NY      %d'%(len(inputx)) ,file=f) 
			# print >> f, ' NG                    251.\n END\n NY      %d'%(40)
			
		for i in range(len(inputx)):
			print ( u'  %0.12f'  %(inputx[i]),file=f)		

		if checkBox.isChecked():
			for i in range(len(inputx)):
				print ( u'  %0.12f' %(inputysqrt[i]),file=f)
				
		else:
			for i in range(len(inputx)):
				print ( u'  %0.12f' %(inputy[i]),file=f)
				
		f.close()
		
		
	def callCONTIN(self):
		global counter, index, check, alpha, distribution, fit,residual
		alpha=[]
		distribution=[]
		fit=[]
		residual=[]
		

		if True:
			self.makecontinIN()
			system('contin.exe <contin.in >contin.out')
	
			self.readcontinOUT()
			self.spinBox.setMaximum(counter)

			index=1


			if check:
				self.graph.changeit()	
			else:
				check=True
				self.graph.drawit()

			self.linealpha.setText(unicode(alpha[index-1]))
			self.spinBox.setValue(1)	
	
		else:
			pass
		
	def readcontinOUT (self):		
		a=open('contin.out','r')

		global alpha, distribution, fit,residual, counter, counterfit, peak,rangea,rangeb,checkBox
		inputx,inputy,inputysqrt=self.inputdata()
		counter=0		
		counterfit=[]
		peak=[]
		for line in a:
			if line[0:7]!='      A': 
				continue
			else:				
					
				for line in a:								
					alpha+=[None]
					alpha[-1]=line[3:11]
					distribution+=[array([0,0,0])] #leaves an extra point at the beginning of the array, corrected with the delete
					fit+=[array([0,0])]
					residual+=[array([0,0])]
					peak.append([])
					counterfit.append(0)
					break							
		
				for line in a:
					if line[0:5]=='    O':
						break
				for line in a:
					if line[0:3]=='   ':
						distribution[-1]=vstack([distribution[-1],genfromtxt(StringIO(line[0:31].replace('D','E')))])
					else:
						distribution[-1]=delete(distribution[-1],0,0)
						distribution[-1]=transpose(distribution[-1])
#
						counter+=1
						break
 #number of peaks at this alpha

				for line in a:
 
					if line[0:5]=='0PEAK':						
						counterfit[-1]+=1
						peak[-1].append([])						
						rangea=line[19:28]  #ranges to be used in the display hovering
						rangea=line[33:42]
						peak[-1][-1].append(float(line[19:28]))
						peak[-1][-1].append(float(line[33:42]))
						for line in a:
							if line[0:20]=='                    ':
								peak[-1][-1].append(float(line[50:68].replace(' ','').replace('X(10**','E')))
								peak[-1][-1].append(float(line[78:85]))
								if len(line)>120:
									if line[126]=='3':
										break
							else:
								peak[-1][-1].append(float(line[50:68].replace(' ','').replace('X(10**','E')))
								peak[-1][-1].append(float(line[78:85]))
								peak[-1][-1].append(float(line[35:42]))

#peak[-1][-1]=[rangea,rangeb,m-1,e-1,m0,e0,m1,e1,m2,e2,std/mean,m3,e3]	of last peak at current alph							
					else:
						break
				for line in a:
					if line[0:5]=='    O':
						break
				for line in a:
					if line[0:3]=='   ':
						fit[-1]=vstack([fit[-1],genfromtxt(StringIO(line[0:22]))])
					else:
						fit[-1]=delete(fit[-1],0,0)
						fit[-1]=transpose(fit[-1])
						
						if checkBox.isChecked():
							residual[-1]=vstack([fit[-1][1][:],inputysqrt-fit[-1][0][:]])
				
						else:
							residual[-1]=vstack([fit[-1][1][:],inputy-fit[-1][0][:]])
							
						break  
		counter-=1			## is thisline where it should be?			
		a.close()				
				
	def export(self):

		global index, data, fit, distribution, alpha,checkBox,fileDialog,check,peak,counterfit,trace,dual
		filename=unicode(fileDialog)
		if check:		
			file=filename+"_%d.czr"%(index)
		else:
			file=filename+".czr"
		
		f=open(file,'w')	  		
		j=0
		if dual:
			if check:	
				print ( u'alpha:	'+alpha[index-1],file=f)
				print ( u'Av.I.CH0:	%0.3e'%(mean(trace[1])),file=f)
				print ( u'Av.I.CH1:	%0.3e'%(mean(trace[3])),file=f)
				
				if checkBox.isChecked():
					print ( u"t	g(normalized)	t	g(normalized 2ndchannel)	t	g(fit)	t	distribution"	,file=f)
					while j<len(distribution[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],data[2][j],data[3][j],data[5][j],\
						fit[index-1][1][j],fit[index-1][0][j],distribution[index-1][2][j],distribution[index-1][0][j]),file=f)
						j+=1

					while j<len(fit[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e		'%(data[0][j],data[2][j],data[3][j],data[5][j],fit[index-1][1][j],fit[index-1][0][j]),file=f)
						j+=1
			
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e				'%(data[0][j],data[2][j],data[3][j],data[5][j]),file=f)
						j+=1
				else:
					print ( u"t	g(data)	t	g(2ndchannel)	t	g(fit)	t	distribution"	,file=f)
					while j<len(distribution[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],\
						data[1][j],data[3][j],data[4][j],fit[index-1][1][j],fit[index-1][0][j],distribution[index-1][2][j],distribution[index-1][0][j]),file=f)
						j+=1

					while j<len(fit[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e		'%(data[0][j],data[1][j],data[3][j],data[4][j],fit[index-1][1][j],fit[index-1][0][j]),file=f)
						j+=1
			
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e				'%(data[3][j],data[4][j]),file=f)
						j+=1	
				print ( u'\n\n\n',file=f)
				i=0
				print ( u"Peak	AV.Time	%Error	Amplitude	%Error"	,file=f)			
				while i <counterfit[index-1]:
					self.I=i+1
					print( u"%d	%0.4e	%0.1e 	%0.4e	%0.1e "\
%(self.I,((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),(math.sqrt(((2*(peak[index-1][i][4])*(peak[index-1][i][5]*\
peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))*((2*(peak[index-1][i][4])*\
(peak[index-1][i][5]*peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))  +  ((1.5*(peak[index-1][i][4])*(peak[index-1][i][4])\
*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))*((1.5*(peak[index-1][i][4])*\
(peak[index-1][i][4])*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*\
(peak[index-1][i][2])))*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))	+  \
  ((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]\
  /peak[index-1][i][6]))*((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))))/((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),\
									peak[index-1][i][2],peak[index-1][i][3])  ,file=f)
					i+=1
				

				
				print ( u'\n\n\n',file=f)
				i=0				
				while i <counterfit[index-1]:
					self.I=i+1
					print ( u"PEAK %d\nSTD. DEV./MEAN = %0.2e\n\
 J   MOMENT(J)  %%ERROR   M(J)/M(J-1) %%ERROR\n\
-1	%0.2e	   %0.1e\n\
 0	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 1	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 2	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 3	 %0.2e	  %0.1e   %0.2e   %0.1e\n"\
					%(self.I,peak[index-1][i][10],peak[index-1][i][2],peak[index-1][i][3],peak[index-1][i][4],\
					peak[index-1][i][5],(peak[index-1][i][4]/peak[index-1][i][2]),(peak[index-1][i][3]+peak[index-1][i][5])\
					,peak[index-1][i][6],peak[index-1][i][7],(peak[index-1][i][6]/peak[index-1][i][4]),(peak[index-1][i][5]+peak[index-1][i][7])\
					,peak[index-1][i][8],peak[index-1][i][9],(peak[index-1][i][8]/peak[index-1][i][6]),(peak[index-1][i][7]+peak[index-1][i][9])\
					,peak[index-1][i][11],peak[index-1][i][12],(peak[index-1][i][11]/peak[index-1][i][8]),(peak[index-1][i][9]+peak[index-1][i][12])),file=f)
					i+=1					
					
			else:	
	
				if checkBox.isChecked():
					print ( u"t	g(datanormalized)	t	g(2ndchannelnormalize)",file=f)
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],data[2][j],data[3][j],data[5][j]),file=f)
						j+=1
				else:
					print( u"t	g(data)	t	g(2ndchannel)",file=f)
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],data[1][j],data[3][j],data[4][j]),file=f)
						j+=1
		
		
		else:
			if check:	
				print ( u'alpha:	'+alpha[index-1],file=f)
				print( u'Av.I.:	%0.3e'%(mean(trace[1])),file=f)
			
				if checkBox.isChecked():
					print ( u"t	g(normalized)	t	g(fit)	t	distribution"	,file=f)
					while j<len(distribution[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],data[2][j],\
						fit[index-1][1][j],fit[index-1][0][j],distribution[index-1][2][j],distribution[index-1][0][j]),file=f)
						j+=1

					while j<len(fit[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e		'%(data[0][j],data[2][j],fit[index-1][1][j],fit[index-1][0][j]),file=f)
						j+=1
			
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e				'%(data[0][j],data[2][j]),file=f)
						j+=1
				else:
					print ( u"t,g(data),t,g(fit),t,distribution"	,file=f)
					while j<len(distribution[index-1][0]):
						print ( u'%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	%0.4e	'%(data[0][j],\
						data[1][j],fit[index-1][1][j],fit[index-1][0][j],distribution[index-1][2][j],distribution[index-1][0][j]),file=f)
						j+=1

					while j<len(fit[index-1][0]):
						print (u'%0.4e	%0.4e	%0.4e	%0.4e		'%(data[0][j],data[1][j],fit[index-1][1][j],fit[index-1][0][j]),file=f)
						j+=1
			
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e				'%(data[0][j],data[1][j]),file=f)
						j+=1	

				print ( u'\n\n\n',file=f)
				i=0
				print ( u"Peak	AV.Time	%Error	Amplitude	%Error"		,file=f)		
				while i <counterfit[index-1]:
					self.I=i+1
					print ( u"%d	%0.4e	%0.1e 	%0.4e	%0.1e "\
%(self.I,((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),(math.sqrt(((2*(peak[index-1][i][4])*(peak[index-1][i][5]*\
peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))*((2*(peak[index-1][i][4])*\
(peak[index-1][i][5]*peak[index-1][i][4])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))  +  ((1.5*(peak[index-1][i][4])*(peak[index-1][i][4])\
*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*(peak[index-1][i][2])))\
*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))*((1.5*(peak[index-1][i][4])*\
(peak[index-1][i][4])*(peak[index-1][i][3]*peak[index-1][i][2])/((peak[index-1][i][2])*\
(peak[index-1][i][2])))*math.sqrt(1/((peak[index-1][i][2])*(peak[index-1][i][6]))))	+  \
  ((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]\
  /peak[index-1][i][6]))*((0.5*(peak[index-1][i][4])*(peak[index-1][i][4])*(peak[index-1][i][7]*peak[index-1][i][6])\
  /((peak[index-1][i][2])*(peak[index-1][i][2])*(peak[index-1][i][6])))*math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))))/((peak[index-1][i][4]/peak[index-1][i][2])*(peak[index-1][i][4]/peak[index-1][i][2])*(math.sqrt(peak[index-1][i][2]/peak[index-1][i][6]))),\
									peak[index-1][i][2],peak[index-1][i][3]),file=f)
					i+=1	
						

				print ( u'\n\n\n',file=f)
				i=0
				while i <counterfit[index-1]:
					self.I=i+1
					print ( u"PEAK %d\nSTD. DEV./MEAN = %0.2e\n\
 J   MOMENT(J)  %%ERROR   M(J)/M(J-1) %%ERROR\n\
-1	%0.2e	   %0.1e\n\
 0	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 1	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 2	 %0.2e	  %0.1e   %0.2e   %0.1e\n\
 3	 %0.2e	  %0.1e   %0.2e   %0.1e\n"\
					%(self.I,peak[index-1][i][10],peak[index-1][i][2],peak[index-1][i][3],peak[index-1][i][4],\
					peak[index-1][i][5],(peak[index-1][i][4]/peak[index-1][i][2]),(peak[index-1][i][3]+peak[index-1][i][5])\
					,peak[index-1][i][6],peak[index-1][i][7],(peak[index-1][i][6]/peak[index-1][i][4]),(peak[index-1][i][5]+peak[index-1][i][7])\
					,peak[index-1][i][8],peak[index-1][i][9],(peak[index-1][i][8]/peak[index-1][i][6]),(peak[index-1][i][7]+peak[index-1][i][9])\
					,peak[index-1][i][11],peak[index-1][i][12],(peak[index-1][i][11]/peak[index-1][i][8]),(peak[index-1][i][9]+peak[index-1][i][12])),file=f)
					i+=1					
					
			else:	
				print ( u'Av.I.:	%0.3e'%(mean(trace[1])),file=f)
				if checkBox.isChecked():
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	'%(data[0][j],data[2][j]),file=f)
						j+=1
				else:
					while j<len(data[0]):
						print ( u'%0.4e	%0.4e	'%(data[0][j],data[1][j]),file=f)
						j+=1		
			
		f.close()
 
 
 

if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
	Continizer = QtWidgets.QMainWindow()
	ui = Ui_Continizer()
	ui.setupUi(Continizer)
	Continizer.show()
	sys.exit(app.exec_())
	
	