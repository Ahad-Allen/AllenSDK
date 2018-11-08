from __future__ import division
import logging
import sys
import functools

import numpy as np
from scipy.ndimage.interpolation import zoom
from six import iteritems

import image_utilities as iu
from base_subimage import PolygonSubImage, SegmentationSubImage


class ClassicCountSubImage(SegmentationSubImage, PolygonSubImage):

    required_polys = ['missing_tile', 'no_signal', 'aav_exclusion']
    required_segmentations = ['segmentation']

    def __init__(self, reduce_level, in_dims, in_spacing, coarse_spacing,
                 polygon_info, segmentation_paths, *args, **kwargs):

        super(ClassicCountSubImage, self).__init__(reduce_level, in_dims, in_spacing,
                                                   coarse_spacing,
                                                   polygon_info=polygon_info,
                                                   segmentation_paths=segmentation_paths,
                                                   *args, **kwargs)


    def process_segmentation(self):

        self.apply_mask('segmentation', 'missing_tile', False)

        self.extract_signal_from_segmentation(signal_name='projection')

        self.apply_mask('projection', 'no_signal', False)
        del self.images['no_signal']

        self.extract_injection_from_segmentation()
        del self.images['segmentation']

        self.binarize('projection')
        self.binarize('injection')


    def compute_injection(self):
        logging.info('computing injection accumulators')

        self.apply_pixel_counter('injection_sum_pixels', self.images['injection'])

        injection_projecting_pixels = np.logical_and(self.images['injection'], self.images['projection'])
        self.apply_pixel_counter('injection_sum_projecting_pixels', injection_projecting_pixels)
        del injection_projecting_pixels

        del self.images['injection']


    def compute_projection(self):
        logging.info('computing projection accumulators')

        self.apply_pixel_counter('sum_projecting_pixels', self.images['projection'])
        del self.images['projection']


    def compute_sum_pixels(self):
        logging.info('computing sum pixel accumulators')

        self.apply_pixel_counter('sum_pixels', np.logical_not(self.images['missing_tile']))

        if 'aav_exclusion' in self.images:
            self.apply_pixel_counter('aav_exclusion_sum_pixels', self.images['aav_exclusion'])


    def compute_coarse_planes(self):

        self.compute_injection()
        self.compute_projection()
        self.compute_sum_pixels()

        del self.images
