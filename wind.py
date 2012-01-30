#!/usr/bin/env python

# @Description: A little hack on visualizing the direction and speed of air currents 
#      	        over North America.



import vtk

## data to read  ####################################################################################
reader = vtk.vtkStructuredPointsReader()
reader.SetFileName("wind.vtk")
reader.Update()

## get the extent of the data and print it ###########################################################
W,H,D = reader.GetOutput().GetDimensions()
print "Reading '%s', width=%i, height=%i, depth=%i" %("wind.vtk", W, H, D)

## creating an outline of the dataset ###############################################################
outline = vtk.vtkOutlineFilter()
outline.SetInput( reader.GetOutput() )

outlineMapper = vtk.vtkPolyDataMapper()
outlineMapper.SetInput( outline.GetOutput() )
outlineActor = vtk.vtkActor()
outlineActor.SetMapper( outlineMapper )
outlineActor.GetProperty().SetColor(1.0,1.0,1.0)
outlineActor.GetProperty().SetLineWidth(2.0)


## find the range of scalars ####################################################################### 
min,max = reader.GetOutput().GetPointData().GetScalars().GetRange()

## a lookup table for mapping point scalar data to colors ##########################################
lut = vtk.vtkColorTransferFunction()
lut.AddRGBPoint(min,         0.0, 0.0, 1.0)
lut.AddRGBPoint(min+(max-min)/4, 0.0, 1.0, 1.0)
lut.AddRGBPoint(min+(max-min)/2, 0.0, 1.0, 0.0)
lut.AddRGBPoint(max-(max-min)/4, 1.0, 1.0, 0.0)
lut.AddRGBPoint(max        , 1.0, 0.0, 0.0)

## a lookup table for coloring glyphs #############################################################
lut2 = vtk.vtkColorTransferFunction()
lut2.AddRGBPoint(min,         .6, .6, .6)
lut2.AddRGBPoint(max,         .6, .6, .6)

## a colorbar to display the colormap #############################################################
scalarBar = vtk.vtkScalarBarActor()
scalarBar.SetLookupTable( lut )
scalarBar.SetTitle( "Wind speed" )
scalarBar.SetOrientationToHorizontal()
scalarBar.GetLabelTextProperty().SetColor(1,1,1)
scalarBar.GetTitleTextProperty().SetColor(1,1,1)

# position of the colorbar in window #
coord = scalarBar.GetPositionCoordinate()
coord.SetCoordinateSystemToNormalizedViewport()
coord.SetValue(0.1,0.05)
scalarBar.SetWidth(.8)
scalarBar.SetHeight(.1)

## define slice plane #############################################################################
SlicePlane = vtk.vtkImageDataGeometryFilter()
SlicePlane.SetInputConnection( reader.GetOutputPort() )
SlicePlane.SetExtent(0, 42, 0, 102, 0, 0)
SlicePlane.ReleaseDataFlagOn()

SlicePlaneMapper = vtk.vtkPolyDataMapper()
SlicePlaneMapper.SetInputConnection( SlicePlane.GetOutputPort() )
SlicePlaneMapper.SetLookupTable( lut )
SlicePlaneActor = vtk.vtkActor()
SlicePlaneActor.SetMapper( SlicePlaneMapper )
SlicePlaneActor.GetProperty().SetOpacity(.6)

## define oriented glyphs #########################################################################
# arrow source for glyph3D #
Arrow = vtk.vtkArrowSource()

glyph = vtk.vtkGlyph3D()
glyph.SetInputConnection( SlicePlane.GetOutputPort() )
glyph.SetSource( Arrow.GetOutput() )
glyph.SetScaleModeToScaleByScalar()
glyph.SetScaleFactor(2)
glyph.ClampingOn()

glyphMapper = vtk.vtkPolyDataMapper()
glyphMapper.SetInputConnection( glyph.GetOutputPort() )
glyphMapper.SetLookupTable( lut2 )
glyphActor = vtk.vtkActor()
glyphActor.SetMapper( glyphMapper )

## define streamlines #############################################################################
# line source for streamline #
LineSource = vtk.vtkLineSource()
LineSource.SetPoint1(17.5, 70.2, 0)
LineSource.SetPoint2(60, 70.2, 0)
LineSource.SetResolution(40)

LineSourceMapper = vtk.vtkPolyDataMapper()
LineSourceMapper.SetInputConnection( LineSource.GetOutputPort() )
LineSourceActor = vtk.vtkActor()
LineSourceActor.SetMapper( LineSourceMapper )

integ = vtk.vtkRungeKutta4() # integrator for generating the streamlines #
streamer = vtk.vtkStreamLine()
streamer.SetInputConnection( reader.GetOutputPort() )
streamer.SetSource( LineSource.GetOutput() )
streamer.SetMaximumPropagationTime(500)
streamer.SetIntegrationStepLength(.02)
streamer.SetStepLength(.01)
streamer.SetIntegrationDirectionToIntegrateBothDirections()
streamer.SetIntegrator( integ )

streamerMapper = vtk.vtkPolyDataMapper()
streamerMapper.SetInputConnection( streamer.GetOutputPort() )
streamerMapper.SetLookupTable( lut )
streamerActor = vtk.vtkActor()
streamerActor.SetMapper( streamerMapper )
streamerActor.VisibilityOn()

## renderer and render window #####################################################################
ren = vtk.vtkRenderer()
ren.SetBackground(.2, .2, .2)
renWin = vtk.vtkRenderWindow()
renWin.SetSize(800, 600)
renWin.AddRenderer( ren )

## render window interactor #######################################################################
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow( renWin )

## add the actors to the renderer #################################################################
ren.AddActor( outlineActor )
ren.AddActor( streamerActor )
ren.AddActor( glyphActor )
ren.AddActor( scalarBar )
ren.AddActor( SlicePlaneActor )
#ren.AddActor( LineSourceActor)

## render #########################################################################################
renWin.Render()

## create window to image filter to get the window to an image ####################################
w2if = vtk.vtkWindowToImageFilter()
w2if.SetInput( renWin )

## create png writer ##############################################################################
wr = vtk.vtkPNGWriter()
wr.SetInput( w2if.GetOutput() )

## Python function for the keyboard interface #####################################################
# count is a screenshot counter #
# level is a plane level counter #
level = 0
count = 0
def Keypress(obj, event):
    global count, iv, level
    key = obj.GetKeySym()
    if key == "s":
        renWin.Render()     
        w2if.Modified() # tell the w2if that it should update #
        fnm = "screenshot%02d.png" %(count)
        wr.SetFileName(fnm)
        wr.Write()
        print "Saved '%s'" %(fnm)
        count = count+1
    # key for moving line source and slice plane #
    elif key == "Up": # moving up the slice plane #
        if level <= 15:
            level = level + 1
            SlicePlane.SetExtent(0, 42, 0, 102, level, level)
            LineSource.SetPoint1(17.5, 70.2, level)
            LineSource.SetPoint2(60, 70.2, level) 
            renWin.Render()
    elif key == "Down": # moving down the slice plane #
        if level >= 0:
            level = level - 1
            SlicePlane.SetExtent(0, 42, 0, 102, level, level)
            LineSource.SetPoint1(17.5, 70.2, level)
            LineSource.SetPoint2(60, 70.2, level) 
            renWin.Render()

## adding keyboard interface, initialize, and start the interactor #################################
iren.AddObserver("KeyPressEvent", Keypress)
iren.Initialize()
iren.Start()
