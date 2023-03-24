Lucid Vision Camera HDR sequence capture program for Total Solar Eclipse 2023
---------------------------------------------------------------------------

High Dynamic Range sequence of three exposures
	This Python script dynamically updating the exposure time in order to
	grab images appropriate for high dynamic range (or HDR) imaging. HDR images
	can be created by combining a number of images acquired at various exposure
	times. This example demonstrates grabbing three images for this purpose,
	without the actual creation of an HDR image.
  
  
Installation:
Download and install ArenaView SDK from LucidVision web https://thinklucid.com/downloads-hub/
- Arena SDK – Win10, 32/64-bit 
- Down load Arena Python Package

Download and install Anaconda python (if not installed already)
Launch Anaconda prompt and do the following:

>>conda create -n "eclipse" python=3.6.8
>>conda activate eclipse
>>cd C:\ProgramData\Lucid Vision Labs\ArenaView\ArenaPy
>>pip install arena_api-*-py3-none-any.whl
>>pip install -r requirements_win.txt

>>cd "C:\ProgramData\Lucid Vision Labs\Examples\src\Python Source Code Examples"
>>python py_acquisition.py

If this script finds camera and reads images from it without error then the camera is working, and is configured properly. 
If not then check camera connections and run ArenaConfig and ArenaView to troubleshoot.   

Now to get HDR exposure: As set of 3 exposures execute 

>>python py_ECLIPSE_HDR.py 

It will create a set of 3 HD exposures saved as FITS file format.
Edit the py_ECLIPSE_HDR script to change the exposure times and save in different name or file format, if needed. 

