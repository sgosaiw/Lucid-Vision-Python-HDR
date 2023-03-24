# -----------------------------------------------------------------------------
# Copyright (c) 2022, Lucid Vision Labs, Inc.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import time
from arena_api.system import system
from arena_api.buffer import BufferFactory
from astropy.io import fits
import numpy as np
import ctypes
import time
'''
Exposure: For High Dynamic Range
	This example demonstrates dynamically updating the exposure time in order to
	grab images appropriate for high dynamic range (or HDR) imaging. HDR images
	can be created by combining a number of images acquired at various exposure
	times. This example demonstrates grabbing three images for this purpose,
	without the actual creation of an HDR image.
'''

'''
=-=-=-=-=-=-=-=-=-
=-=- SETTINGS =-=-
=-=-=-=-=-=-=-=-=-
'''
TAB1 = "  "
TAB2 = "    "
num_images = 5
exp1 = 40000.0
exp2 = 20000.0
exp3 = 5000.0


def create_devices_with_tries():
	'''
	Waits for the user to connect a device before raising an
		exception if it fails
	'''
	tries = 0
	tries_max = 6
	sleep_time_secs = 10
	devices = None
	while tries < tries_max:  # Wait for device for 60 seconds
		devices = system.create_device()
		if not devices:
			print(
				f'Try {tries+1} of {tries_max}: waiting for {sleep_time_secs} '
				f'secs for a device to be connected!')
			for sec_count in range(sleep_time_secs):
				time.sleep(1)
				print(f'{sec_count + 1 } seconds passed ',
					'.' * sec_count, end='\r')
			tries += 1
		else:
			return devices
	else:
		raise Exception(f'No device found! Please connect a device and run '
						f'the example again.')

def tic():
	return time.time()

def toc(t_start):
	return time.time() - t_start

def store_initial(nodemap):
	'''
	Store initial node values, return their values at the end
	'''
	nodes = nodemap.get_node(['TriggerMode', 'TriggerSource',
							'TriggerSelector', 'TriggerSoftware',
							'TriggerArmed', 'ExposureAuto', 'ExposureTime','PixelFormat','Width','Height',
							'AcquisitionFrameRateEnable','AcquisitionFrameRate'])

	trigger_mode_initial = nodes['TriggerMode'].value
	trigger_source_initial = nodes['TriggerSource'].value
	trigger_selector_initial = nodes['TriggerSelector'].value
	exposure_auto_initial = nodes['ExposureAuto'].value
	exposure_time_initial = nodes['ExposureTime'].value

	return nodes, [exposure_time_initial, exposure_auto_initial,
				trigger_selector_initial, trigger_source_initial,
				trigger_mode_initial]


def trigger_software_once_armed(nodes):
	'''
	Continually check until trigger is armed. Once the trigger is armed,
		it is ready to be executed.
	'''
	trigger_armed = False

	while (trigger_armed is False):
		trigger_armed = bool(nodes['TriggerArmed'].value)

	# retrieve and execute software trigger node
	nodes['TriggerSoftware'].execute()


def acquire_hdr_images(device, nodes, initial_vals, exp1, exp2, exp3):
	'''
	demonstrates exposure configuration and acquisition for HDR imaging
	(1) Sets trigger mode
	(2) Disables automatic exposure
	(3) Sets high exposure time
	(4) Gets first image
	(5) Sets medium exposure time
	(6) Gets second image
	(7) Sets low exposure time
	(8) Gets third images
	(9) Copies images into object for later processing
	(10) Does NOT process copied images
	(11) Cleans up copied images
	'''
	'''
	Prepare trigger mode
		Enable trigger mode before starting the stream. This example uses the
		trigger to control the moment that images are taken. This ensures the
		exposure time of each image in a way that a continuous stream might have
		trouble with.
	'''
	print(f"{TAB1}Prepare trigger mode")
	nodes['TriggerSelector'].value = "FrameStart"
	nodes['TriggerMode'].value = "On"
	nodes['TriggerSource'].value = "Software"
	nodes['AcquisitionFrameRateEnable'].value=True
	min_frame_rate = nodes['AcquisitionFrameRate'].min
	max_frame_rate = nodes['AcquisitionFrameRate'].max
	frame_rate = 1000000.0 / exp1
	
	if min_frame_rate <= frame_rate <= max_frame_rate:
		nodes['AcquisitionFrameRate'].value = frame_rate
		print(f"Frame rate is set to : {frame_rate}")
	else:
		print(f"Frame rate {frame_rate} is out of the allowed range ({min_frame_rate}, {max_frame_rate})")
		frame_rate=nodes['AcquisitionFrameRate'].max
		print(f"Frame rate is set to max rate: {max_frame_rate}")
		nodes['AcquisitionFrameRate'].value=frame_rate
	

	'''
	Disable automatic exposure
		Disable automatic exposure before starting the stream. The HDR images in
		this example require three images of varied exposures, which need to be
		set manually.
	'''
	print(f"{TAB1}Disable auto exposure")
	nodes['ExposureAuto'].value = 'Off'
	pixel_format_name = 'Mono12'
	print(f'Setting Pixel Format to {pixel_format_name}')
	nodes['PixelFormat'].value=pixel_format_name
	'''
	Get exposure time and software trigger nodes
		The exposure time and software trigger nodes are retrieved beforehand in
		order to check for existance, readability, and writability only once
		before the stream.
	'''
	print(f"{TAB1}Get exposure time and trigger software nodes")

	if nodes['ExposureTime'] is None or nodes['TriggerSoftware'] is None:
		raise Exception("ExposureTime or TriggerSoftware node not found")

	if (nodes['ExposureTime'].is_writable is False
	or nodes['TriggerSoftware'].is_writable is False):
		raise Exception("ExposureTime or TriggerSoftware node not writable")

	'''
	If largest exposure times is not within the exposure time range, set
		largest exposure time to max value and set the remaining exposure times
		to half the value of the state before
	'''
	exposures=[exp1,exp2,exp3]

	if (exp1 > nodes['ExposureTime'].max
	or exp3 < nodes['ExposureTime'].min):

		exp1 = nodes['ExposureTime'].max
		#exp2 = exp1 / 2.
		#exp3 = exp2 / 2.
		print(f"Exceeded Max exposure time of: {nodes['ExposureTime'].max}")			

	exposures=[exp1,exp2,exp3]
	print(f"New exposure times are : {exposures}")
	'''
	Setup stream values
	'''
	tl_stream_nodemap = device.tl_stream_nodemap
	tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True
	tl_stream_nodemap['StreamPacketResendEnable'].value = True

	# Store HDR images for processing
	#hdr_images = []
	#datacub=[] #np.zeros((num_images*len(exposures),2048,2448))

	print(f"{TAB1}Acquire {num_images} HDR images")
	device.start_stream()

	for i in range(0, num_images):
		'''
		Get high, medium, and low exposure images
			This example grabs three examples of varying exposures for later
			processing. For each image, the exposure must be set, an image must
			be triggered, and then that image must be retrieved. After the
			exposure time is changed, the setting does not take place on the
			device until after the next frame. Because of this, two images are
			retrieved, the first of which is discarded.
		'''
		print(f'{TAB2}Getting HDR image set {i}')

		for j, exposure in enumerate(exposures):
			#set exposure time
			print(f"{TAB1}{TAB2}Image Exposure{j+1}: {exposure} ms")
			nodes['ExposureTime'].value=exposure
			trigger_software_once_armed(nodes)
			image_pre=device.get_buffer()
			trigger_software_once_armed(nodes)
			image=device.get_buffer()

			#print(f' Width X Height ='f'{image.width} x {image.height}')
			#print('Converting image buffer to a numpy array')
			pdata_as16 = ctypes.cast(image.pdata,ctypes.POINTER(ctypes.c_ushort))
			nparray_reshaped = np.ctypeslib.as_array(pdata_as16,(image.height, image.width))
			#print('Saving image')
			#print(nparray_reshaped.shape)
			img_fits = fits.PrimaryHDU(nparray_reshaped)
			img_fits.writeto(f'hdr_image_{i}_{j + 1}.fits', overwrite=True)
			'''
			Copy images for processing later
			Use the image factory to copy the images for later processing. Images
			are copied in order to requeue buffers to allow for more images to be
			retrieved from the device.
			'''
			# Requeue buffers
			device.requeue_buffer(image_pre)
			device.requeue_buffer(image)

	device.stop_stream()

	'''
	Run HDR processing
		Once the images have been retrieved and copied, they can be processed
		into an HDR image. HDR algorithms
	'''
	#print(f"{TAB1}Run HDR processing")

	# Destroy copied images after processing to prevent memory leaks
	#for i in range(0, hdr_images.__len__()):
	#	BufferFactory.destroy(hdr_images[i])

	'''
	Return nodes to initial values
	'''
	nodes['ExposureTime'].value = initial_vals[0]
	nodes['ExposureAuto'].value = initial_vals[1]
	nodes['TriggerSelector'].value = initial_vals[2]
	nodes['TriggerSource'].value = initial_vals[3]
	nodes['TriggerMode'].value = initial_vals[4]

	#return np.array(datacub)

def example_entry_point():

	devices = create_devices_with_tries()
	device = devices[0]

	nodemap = device.nodemap
	nodes, initial_vals = store_initial(nodemap)
	t_start=tic()
	print(f"at time: {t_start}")
	acquire_hdr_images(device, nodes, initial_vals, exp1, exp2, exp3)

	t_elapsed=toc(t_start)
	print(f"Time elapsed: {t_elapsed} seconds")

	system.destroy_device(device)


if __name__ == "__main__":
	print("Eclipse sequence Started\n")
	example_entry_point()
	print("\nEclipse sequence Completed")
