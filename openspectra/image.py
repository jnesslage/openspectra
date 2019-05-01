#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import logging
from enum import Enum
from typing import Union

import numpy as np

from openspectra.utils import LogHelper, OpenSpectraDataTypes, OpenSpectraProperties, Logger


class Band(Enum):
    GREY = None
    RED = 1
    GREEN = 2
    BLUE = 3


class RGBLimits:

    def __init__(self, red:Union[int, float], green:Union[int, float], blue:Union[int, float]):
        self.__red:Union[int, float] = red
        self.__green:Union[int, float] = green
        self.__blue:Union[int, float] = blue

    def red(self) -> Union[int, float]:
        return self.__red

    def green(self) -> Union[int, float]:
        return self.__green

    def blue(self) -> Union[int, float]:
        return self.__blue


class ImageAdjuster:

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band):
        pass

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band):
        pass

    def adjust(self):
        pass

    def low_cutoff(self, band:Band) -> Union[Union[int, float], RGBLimits]:
        pass

    def set_low_cutoff(self, limit:Union[int, float], band:Band):
        pass

    def high_cutoff(self, band:Band) -> Union[Union[int, float], RGBLimits]:
        pass

    def set_high_cutoff(self, limit:Union[int, float], band:Band):
        pass

    def is_updated(self, band:Band) -> bool:
        pass


class BandImageAdjuster(ImageAdjuster):

    __LOG:Logger = LogHelper.logger("BandImageAdjuster")

    def __init__(self, band:np.ndarray):
        self.__band = band
        self.__type = self.__band.dtype
        self.__image_data = None
        self.__low_cutoff = 0
        self.__high_cutoff = 0
        self.adjust_by_percentage(2, 98)
        self.__updated = True
        self.adjust()
        BandImageAdjuster.__LOG.debug("type: {0}", self.__type)
        BandImageAdjuster.__LOG.debug("min: {0}, max: {1}", self.__band.min(), self.__band.max())

    def __del__(self):
        self.__image_data = None
        self.__band = None

    def adjusted_data(self) -> np.ndarray:
        return self.__image_data

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """band is ignore here if passed"""
        if self.__type in OpenSpectraDataTypes.Ints:
            self.__low_cutoff, self.__high_cutoff = np.percentile(self.__band, (lower, upper))
            self.__updated = True
        elif self.__type in OpenSpectraDataTypes.Floats:
            self.__calculate_float_cutoffs(lower, upper)
            self.__updated = True
        else:
            raise TypeError("Image data type {0} not supported".format(self.__type))

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """band is ignore here if passed"""
        self.__low_cutoff = lower
        self.__high_cutoff = upper
        self.__updated = True

    def low_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        """band is ignore here if passed"""
        return self.__low_cutoff

    def set_low_cutoff(self, limit, band:Band=None):
        """band is ignore here if passed"""
        self.__low_cutoff = limit
        self.__updated = True

    def high_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        """band is ignore here if passed"""
        return self.__high_cutoff

    def set_high_cutoff(self, limit, band:Band=None):
        """band is ignore here if passed"""
        self.__high_cutoff = limit
        self.__updated = True

    def adjust(self):
        if self.__updated:
            BandImageAdjuster.__LOG.debug("low cutoff: {0}, high cutoff: {1}", self.low_cutoff(), self.high_cutoff())

            # TODO <= or <, looks like <=, with < I get strange dots on the image
            low_mask = np.ma.getmask(np.ma.masked_where(self.__band <= self.__low_cutoff, self.__band, False))

            # TODO >= or <, looks like >=, with < I get strange dots on the image
            high_mask = np.ma.getmask(np.ma.masked_where(self.__band >= self.__high_cutoff, self.__band, False))

            full_mask = low_mask | high_mask
            masked_band = np.ma.masked_where(full_mask, self.__band, True)

            # 0 and 256 assumes 8-bit images, the pixel value limits
            # TODO why didn't 255 work?
            A, B = 0, 256
            masked_band = ((masked_band - self.__low_cutoff) * ((B - A) / (self.__high_cutoff - self.__low_cutoff)) + A)

            masked_band[low_mask] = 0
            masked_band[high_mask] = 255

            self.__image_data = masked_band.astype("uint8")
            self.__updated = False

    def is_updated(self, band:Band=None) -> bool:
        """Returns true if the image parameters have been updated but adjust()
        has not been called.  The band parameter is ignored here"""
        return self.__updated

    def __calculate_float_cutoffs(self, lower:Union[int, float], upper:Union[int, float]):
        nbins = OpenSpectraProperties.FloatBins
        min = self.__band.min()
        max = self.__band.max()

        # scale to generate histogram data
        hist_scaled = np.floor((self.__band - min)/(max - min) * (nbins - 1))
        scaled_low_cut, scaled_high_cut = np.percentile(hist_scaled, (lower, upper))

        self.__low_cutoff = (scaled_low_cut / (nbins - 1) * (max - min)) + min
        self.__high_cutoff = (scaled_high_cut / (nbins - 1) * (max - min)) + min


class RGBImageAdjuster(ImageAdjuster):

    def __init__(self, red: np.ndarray, green: np.ndarray, blue: np.ndarray):
        self.__adjusted_bands = {Band.RED: BandImageAdjuster(red),
                                 Band.GREEN: BandImageAdjuster(green),
                                 Band.BLUE: BandImageAdjuster(blue)}

    def __del__(self):
        del self.__adjusted_bands

    def _adjusted_data(self, band:Band) -> np.ndarray:
        return self.__adjusted_bands[band].adjusted_data()

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is not None:
            self.__adjusted_bands[band].adjust_by_percentage(lower, upper)
        else:
            self.__adjusted_bands[Band.RED].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_percentage(lower, upper)

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_value(lower, upper)
        else:
            self.__adjusted_bands[band].adjust_by_value(lower, upper)

    def adjust(self):
        """Adjust all three bands, if the band is not out of date
        no adjustment calculation will be made"""
        self.__adjusted_bands[Band.RED].adjust()
        self.__adjusted_bands[Band.GREEN].adjust()
        self.__adjusted_bands[Band.BLUE].adjust()

    def low_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        if band is None:
            return RGBLimits(self.__adjusted_bands[Band.RED].low_cutoff(),
                    self.__adjusted_bands[Band.GREEN].low_cutoff(),
                    self.__adjusted_bands[Band.BLUE].low_cutoff())
        else:
            return self.__adjusted_bands[band].low_cutoff()

    def set_low_cutoff(self, limit:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].set_low_cutoff(limit)
            self.__adjusted_bands[Band.GREEN].set_low_cutoff(limit)
            self.__adjusted_bands[Band.BLUE].set_low_cutoff(limit)
        else:
            self.__adjusted_bands[band].set_low_cutoff(limit)

    def high_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        if band is None:
            return RGBLimits(self.__adjusted_bands[Band.RED].high_cutoff(),
                    self.__adjusted_bands[Band.GREEN].high_cutoff(),
                    self.__adjusted_bands[Band.BLUE].high_cutoff())
        else:
            return self.__adjusted_bands[band].high_cutoff()

    def set_high_cutoff(self, limit:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].set_high_cutoff(limit)
            self.__adjusted_bands[Band.GREEN].set_high_cutoff(limit)
            self.__adjusted_bands[Band.BLUE].set_high_cutoff(limit)
        else:
            self.__adjusted_bands[band].set_high_cutoff(limit)

    def is_updated(self, band:Band=None) -> bool:
        """Returns True if any of the bands or the passed band have had
        their parameters updated but the band has not had adjust() called"""
        if band is not None:
            self.__adjusted_bands[band].is_updated()
        else:
            return self.__adjusted_bands[Band.RED].is_updated() or \
                self.__adjusted_bands[Band.GREEN].is_updated() or \
                self.__adjusted_bands[Band.BLUE].is_updated()


# TODO need to think through how much data we're holding here, clean up, views?
class Image(ImageAdjuster):

    def image_data(self, band:Band) -> np.ndarray:
        pass

    def raw_data(self, band:Band) -> np.ndarray:
        pass

    def image_shape(self) -> (int, int):
        pass

    def bytes_per_line(self) -> int:
        pass

    def label(self, band:Band) -> str:
        pass


class GreyscaleImage(Image, BandImageAdjuster):
    """An 8-bit 8-bit grayscale image"""
    def __init__(self, band:np.ndarray, label:str=None):
        super().__init__(band)
        self.__band = band
        self.__label = label

    def __del__(self):
        super().__del__()
        self.__label = None
        self.__band = None

    def adjusted_data(self) -> np.ndarray:
        """Do not call this method, it's an unfortunate consequence of needing
        it to be public on BandImageAdjuster for use by RGBImageAdjuster"""
        raise NotImplementedError("Do not call GreyscaleImage.adjusted_data(), use GreyscaleImage.image_data() instead")

    def image_data(self, band:Band=None) -> np.ndarray:
        """band is ignored here if passed"""
        if self.is_updated():
            self.adjust()
        return super().adjusted_data()

    # TODO Warning returns view of the original data?!
    def raw_data(self, band:Band=None) -> np.ndarray:
        """band is ignored here if passed"""
        return self.__band

    def image_shape(self) -> (int, int):
        return self.image_data().shape

    def bytes_per_line(self) -> int:
        return self.image_data().shape[1]

    def label(self, band:Band=None) -> str:
        """band is ignored here if passed"""
        return self.__label


# TODO this is definately not thread safe
class RGBImage(Image, RGBImageAdjuster):
    """A 32-bit RGB image using format (0xffRRGGBB)"""

    __LOG:Logger = LogHelper.logger("RGBImage")

    __HIGH_BYTE = 255 * 256 * 256 * 256
    __RED_SHIFT = 256 * 256
    __GREEN_SHIFT = 256

    def __init__(self, red:np.ndarray, green:np.ndarray, blue:np.ndarray,
            red_label:str=None, green_label:str=None, blue_label:str=None):
        if not ((red.size == green.size == blue.size) and
                (red.shape == green.shape == blue.shape)):
            raise ValueError("All bands must have the same size and shape")
        super().__init__(red, green, blue)

        self.__labels = {Band.RED: red_label, Band.GREEN: green_label, Band.BLUE: blue_label}
        self.__label:str = ""
        if red_label is not None: self.__label += red_label + " "
        if green_label is not None: self.__label += green_label + " "
        if blue_label is not None: self.__label += blue_label
        if self.__label is not None: self.__label = self.__label.strip()

        self.__bands = {Band.RED: red, Band.GREEN: green, Band.BLUE: blue}
        self.__high_bytes = np.full(red.shape, RGBImage.__HIGH_BYTE, np.uint32)

        self.__calculate_image()

        if RGBImage.__LOG.isEnabledFor(logging.DEBUG):
            np.set_printoptions(8, formatter={'int_kind': '{:02x}'.format})
            RGBImage.__LOG.debug("{0}", self.__image_data)
            RGBImage.__LOG.debug("height: {0}", self.__image_data.shape[0])
            RGBImage.__LOG.debug("width: {0}", self.__image_data.shape[1])
            RGBImage.__LOG.debug("size: {0}", self.__image_data.size)
            np.set_printoptions()

    def __del__(self):
        super().__del__()
        self.__image_data = None
        self.__high_bytes = None
        self.__label = None
        del self.__labels
        del self.__bands

    def adjust(self):
        if super().is_updated():
            super().adjust()
            self.__calculate_image()

    def image_data(self, band:Band=None) -> np.ndarray:
        """If band is None returns all three bands as a single image data set
        If band is supplied returns the adjusted image data for that band"""
        if super().is_updated():
            super().adjust()
            self.__calculate_image()

        if band is not None:
            return self._adjusted_data(band)
        else:
            return self.__image_data

    # TODO Warning returns view of the original data?!
    def raw_data(self, band:Band) -> np.ndarray:
        # TODO so this returns a view that could allow the user to alter the underlying data
        # TODO Although I'm not sure what that would do in the case of a memmap??
        return self.__bands[band]

    def image_shape(self) -> (int, int):
        return self.__image_data.shape

    def bytes_per_line(self) -> int:
        return self.__image_data.shape[1] * 4

    def label(self, band:Band=None) -> str:
        if band is None:
            return self.__label
        else:
            return self.__labels[band]

    def __calculate_image(self):
        self.__image_data = self.__high_bytes + \
                            self._adjusted_data(Band.RED).astype(np.uint32) * RGBImage.__RED_SHIFT + \
                            self._adjusted_data(Band.GREEN).astype(np.uint32) * RGBImage.__GREEN_SHIFT + \
                            self._adjusted_data(Band.BLUE).astype(np.uint32)
