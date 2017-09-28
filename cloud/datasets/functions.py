import datetime
from functools import lru_cache
import os

# You can install this module via 'pip3 install --user ephem' on mistral. Make sure that you are using
# a new version of gcc. You can test this via 'gcc --version'. You should use at least v7.1 ('module load gcc/7.1.0')
from pysolar import solar

import numpy as np
#from PIL import Image, ImageDraw, ImageOps, ImageFont
from scipy.interpolate import interp1d
import math

#import matplotlib.dates as mdate
#import datetime
#import glob
#from time import clock
#import copy
#from Converter import convert

def process_cloud_cover(datasets, filename, timestamp, threshold_temperature=18):
    """ Returns the cloud cover of a given image.

    This method takes a file, reads and processes the content. It returns a tuple with the
    filename, timestamp of the file and the cloud cover ratio.

    Args:
        args: A tuple of two tuples. The first should contain the file name and the timestamp. The second should
            contain the threshold temperature (declares whether there is a cloud or not).

    Returns:
        Tuple with filename, timestamp and cloud cover ratio.
    """

    import numpy as np

    data = datasets.read(filename)

    # Calculate Cloud Cover
    cover_number = np.sum(data > threshold_temperature)
    #if dataset.mask_transparent_pixels != 0:
    #    cloud_cover = 100. * float(cover_number) / float(dataset.mask_transparent_pixels)
    #else:
    cloud_cover = 100. * float(cover_number) / float(data.size)

    return filename, timestamp, cloud_cover


@lru_cache(maxsize=32)
def calculate_SI_parameter(size=100):
    """ Calculates the SI parameter.

    This function is cached. Even if it is called many times, it calculates the SI parameter only once.

    Args:
        size: The size of the SI parameter.

    Returns:
        A numpy.array with the SI parameters.
    """
    parameter = np.zeros(size)
    for j in range(size):
        parameter[j] = (0 + j * 0.4424283716980435 - pow(j, 2) * 0.06676211439554262 + pow(j,
                                                                                           3) * 0.0026358061791573453 - pow(
            j, 4) * 0.000029417130873311177 + pow(j, 5) * 1.0292852149593944e-7) * 0.001

    return parameter

def cloudiness(datasets, dataset_name, filename, timestamp, si_parameter, scale_factor=0.1):#, InputFilePath):
    """ Calculates the cloud coverage of a given cloud cam image.

    Preliminary version of the All-Sky Cloud Algorithms (ASCA)
    The code is based on the analysis of every single pixel on a jpeg-Image.
    The used Ski-Index and Brightness-Index base on Letu et al. (2014), Applied Optics, Vol. 53, No. 31.

    Please ask before sharing this code!

    The original code is written by Marcus Klingebiel, March 2016
    Max-Planck-Institute for Meteorology
    E-Mail: marcus.klingebiel@mpimet.mpg.de

    Code edited by Tobias Machnitzki
    Email: tobias-machnitzki@web.de

    Code refactored by John Mrziglod, June 2017
    Email: mrzo@gmx.de

    Args:
        datasets:
        dataset_name:
        filename:
        timestamp:

    Returns:

    """
    
    print("!!!!!!!!!!!!!!!!!!Running ASCA!!!!!!!!!!!!!!!!!")

    # --------------------Settings------------------------------------------------------------------------------------------

    debugger = False  # if true, the program will print a message after each step

    TXTFile = False  # if True, the program will generate a csv file with several information. Delimiter = ','

    #    imagefont_size = 20 #Sets the font size of everything written into the picture

    Radius_synop = True  # If True: not the whole sky will be used, but just the 60 degrees from the middle on (like the DWD does with cloud covering)

    Save_image = False  # If True: an image will be printed at output-location, where recognized clouds are collored.

    #    font = ImageFont.truetype("/home/tobias/anaconda3/lib/python3.5/site-packages/matplotlib/mpl-data/fonts/ttf/Vera.ttf",imagefont_size)    # Font

    set_scale_factor = 10  # this factor sets the acuracy of the program. By scaling down the image size the program gets faster but also its acuracy dercreases.
    # It needs to be between 1 and 100. If set 100, then the original size of the image will be used.
    # If set to 50 the image will be scaled down to half its size
    #

    # ----------------------Read files------------------------------------------------------------------------------------------------------

    OutputPath = "/media/MPI/ASCA/images/s160521/out/"

    cloudiness_value = []
    ASCAtime = []


    # ------------Calculate SZA--------------------------------------------------------------------------------------------------------------
    if debugger:
        print("Calculating SZA")

    # Calculate the solar zenith angle
    lat, lon = datasets.get_location(timestamp)
    local_timestamp = timestamp + datetime.timedelta(hours=int(lon / 15))
    sza = solar.get_altitude(lat, lon, local_timestamp)

    #return filename, timestamp, altitude

    if sza > 85:  # The program will only process images made at daylight
        return filename, timestamp, 0

    azimuth = solar.get_azimuth(lat, lon, local_timestamp)
    sza_orig = sza
    azi_orig = azimuth
    azimuth = azimuth + 190  # 197 good
    print(str(sza) + '   ' + Hour_str + ':' + Minute_str)
    if azimuth > 360:
        azimuth = azimuth - 360


    # ---Read image and set some parameters-------------------------------------------------------------------------------------------------
    if debugger:
        print("Reading image and setting parameters")

    image = datasets.read(dataset_name, filename, apply_mask=True)

    # ------------rescale picture-------------------------------------------

    """x_size_raw = image.size[0]
    y_size_raw = image.size[1]
    NEW_SIZE = (x_size_raw * scale_factor, y_size_raw * scale_factor)
    image.thumbnail(NEW_SIZE, Image.ANTIALIAS)

    image = ImageOps.mirror(image)  # Mirror picture

    x_size = image.size[0]
    y_size = image.size[1]"""
    x_center = int(image.shape[0] / 2)  # Detect center of the true image
    y_center = int(image.shape[1] / 2)
    radius = 900  # pixel    #  Set area for the true allsky image

    scale = image.shape[0] / 2592.

    # -------------convert image to an array and remove unnecessary part around true allsky image-----------------------------------------------------------------
    if debugger:
        print("Drawing circle around image and removing the rest")

    """r = radius * scale
    y, x = np.ogrid[-y_mittel:y_size - y_mittel, -x_mittel:x_size - x_mittel]
    x = x + (15 * scale)  # move centerpoint manually
    y = y - (40 * scale)
    mask = x ** 2 + y ** 2 <= r ** 2  # make a circular boolean array which is false in the area outside the true allsky image

    image_array = np.asarray(image,
                             order='F')  # converting the image to an array with array[x,y,color]; color: 0=red, 1,green, 2=blue
    image_array.setflags(write=True)  # making it able to work with that array and change it
    image_array[:, :, :][~mask] = [0, 0, 0]  # using the mask created before on that new made array

    if Radius_synop:
        mask = x ** 2 + y ** 2 <= (765 * scale) ** 2
        image_array[:, :, :][~mask] = [0, 0, 0]

    del x, y"""
    #
    # ------------Calculate position of sun on picture---------------------------------------------------------------------------------------
    if debugger:
        print("Calculating position of the sun on picture")

    sza = sza - 90
    if sza < 0:
        sza = sza * (-1)

    azimuth_angle = ((2 * math.pi) / 360) * (azimuth - 90)
    sza = ((2 * math.pi) / 360) * sza
    x_sol_cen = x_center - (15 * scale)
    y_sol_cen = y_center + (40 * scale)
    RadiusBild = r
    sza_dist = RadiusBild * math.cos(sza)

    x = x_sol_cen - sza_dist * math.cos(azimuth_angle)
    y = y_sol_cen - sza_dist * math.sin(azimuth_angle)

    ###-----------Draw circle around position of sun-------------------------------------------------------------------------------------------
    if debugger:
        print("Drawing circle around position of sun")

    x_sol_cen = int(x)
    y_sol_cen = int(y)
    Radius_sol = 300 * scale
    Radius_sol_center = 250 * scale

    y, x = np.ogrid[-y_sol_cen:y_size - y_sol_cen, -x_sol_cen:x_size - x_sol_cen]
    sol_mask = x ** 2 + y ** 2 <= Radius_sol ** 2
    sol_mask_cen = x ** 2 + y ** 2 <= Radius_sol_center ** 2
    sol_mask_cen1 = sol_mask_cen
    image_array[:, :, :][sol_mask_cen] = [0, 0, 0]
    #        image_array[:,:,:][]

    ##-------Calculate Sky Index SI and Brightness Index BI------------Based on Letu et al. (2014)-------------------------------------------------
    if debugger:
        print("Calculating Sky Index SI and Brightness Index BI")

    image_array_f = image_array.astype(float)

    SI = ((image_array_f[:, :, 2]) - (image_array_f[:, :, 0])) / (
    ((image_array_f[:, :, 2]) + (image_array_f[:, :, 0])))
    where_are_NaNs = np.isnan(SI)
    SI[where_are_NaNs] = 1

    mask_sol1 = SI < 0.1
    Radius = 990 * scale
    sol_mask_double = x ** 2 + y ** 2 <= Radius ** 2
    mask_sol1 = np.logical_and(mask_sol1, ~sol_mask_double)
    image_array[:, :, :][mask_sol1] = [255, 0, 0]

    ###-------------Include area around the sun----------------------------------------------------------------------------------------------------
    if debugger:
        print("Including area around the sun")

    y, x = np.ogrid[-y_sol_cen:y_size - y_sol_cen, -x_sol_cen:x_size - x_sol_cen]
    sol_mask = x ** 2 + y ** 2 <= Radius_sol ** 2
    sol_mask_cen = x ** 2 + y ** 2 <= Radius_sol_center ** 2
    sol_mask_cen = np.logical_and(sol_mask_cen, sol_mask)

    Radius_sol = size * 100 * 2
    sol_mask = x ** 2 + y ** 2 <= Radius_sol ** 2
    mask2 = np.logical_and(~sol_mask_cen, sol_mask)

    image_array_c = copy.deepcopy(
        image_array)  # duplicating array: one for counting one for printing a colored image

    time3 = clock()

    for j in range(size):
        Radius_sol = j * 10 * scale
        sol_mask = (x * x) + (y * y) <= Radius_sol * Radius_sol
        mask2 = np.logical_and(~sol_mask_cen, sol_mask)
        sol_mask_cen = np.logical_or(sol_mask, sol_mask_cen)

        mask3 = SI < parameter[j]
        mask3 = np.logical_and(mask2, mask3)
        image_array_c[mask3] = [255, 0, 0]
        image_array[mask3] = [255, 300 - 3 * j, 0]

    time4 = clock()
    #        print 'Schleifenzeit:', time4-time3
    ##---------Count red pixel(clouds) and blue-green pixel(sky)-------------------------------------------------------------------------------------------
    if debugger:
        print("Counting red pixel for sky and blue for clouds")

    c_mask = np.logical_and(~sol_mask_cen1, mask)
    c_array = (
    image_array_c[:, :, 0] + image_array_c[:, :, 1] + image_array_c[:, :, 2])  # array just for the counting
    Count1 = np.shape(np.where(c_array == 255))[1]
    Count2 = np.shape(np.where(c_mask == True))[1]

    CloudinessPercent = (100 / float(Count2) * float(Count1))
    CloudinessSynop = int(round(8 * (float(Count1) / float(Count2))))

    image = Image.fromarray(image_array.astype(np.uint8))

    # ----------Mirror Image-----------------------------
    image = ImageOps.mirror(image)  # Mirror Image back
    # ---------Add Text-----------------------------------
    if debugger:
        print("Adding text")

    sza = "{:5.1f}".format(sza_orig)
    azimuth = "{:5.1f}".format(azi_orig)
    CloudinessPercent = "{:5.1f}".format(CloudinessPercent)

    #            draw = ImageDraw.Draw(image)
    #            draw.text((20*scale, 20*scale),"BCO All-Sky Camera",(255,255,255),font=font)
    #            draw.text((20*scale, 200*scale),Hour_str+":"+Minute_str+' UTC',(255,255,255),font=font)
    #
    #            draw.text((20*scale, 1700*scale),"SZA = "+str(sza)+u'\u00B0',(255,255,255),font=font)
    #            draw.text((20*scale, 1820*scale),"Azimuth = "+str(azimuth)+u'\u00B0',(255,255,255),font=font)
    #
    #            draw.text((1940*scale, 1700*scale),"Cloudiness: ",(255,255,255),font=font)
    #            draw.text((1930*scale, 1820*scale),str(CloudinessPercent)+'%   '+ str(CloudinessSynop)+'/8',(255,255,255),font=font)
    #
    #            draw.text((1990*scale, 20*scale),Day_str+'.'+Month_str+'.20'+Year_str,(255,255,255),font=font)

    # -------------Save values to csv-File---------------------------------------
    #            if debugger:
    #                print "Saving values to csv-File"

    #            EpochTime=(datetime.datetime(2000+Year,Month,Day,Hour,Minute,Second) - datetime.datetime(1970,1,1)).total_seconds()
    #            f.write(str(EpochTime)+', '+Hour_str+':'+Minute_str+', '+str(sza)+', '+str(azimuth)+', '+str(CloudinessPercent)+', '+str(CloudinessSynop)+'\n')
    # -------------Save picture--------------------------------------------------
    if Save_image:
        if debugger:
            print("saving picture")

        image = convert(filename, image, OutputPath)
        image.save(
            OutputPath + Year_str + Month_str + Day_str + '_' + Hour_str + Minute_str + Second_str + '_ASCA.jpg')

    # image.show()
    time2 = clock()
    time = time2 - time1
    cloudiness_value.append(CloudinessPercent)
    ASCAtime.append(mdate.date2num(datetime.datetime(Year + 2000, Month, Day, Hour, Minute, Second)))

        #               print "Berechnungszeit: ", time
    return filename, timestamp, cloudiness_value


def rename(dataset, filename, timestamp, new_filename_template):
    new_filename = dataset.generate_filename_from_date(new_filename_template, timestamp)
    return (timestamp, filename, new_filename)
    #os.rename(filename, new_filename)