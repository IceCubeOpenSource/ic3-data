from __future__ import print_function, division
import numpy as np

from ic3_data.utils.autoencoder import autoencoder
from ic3_data.misc import weighted_quantile, weighted_std

"""All data format functions must have the following signature:

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """


def charge_bins(dom_charges, rel_dom_times, global_time_offset,
                local_time_offset, config, *args, **kwargs):
    """Histogram charge in time bins as given by config['time_bins'].

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """
    bin_values_list = []
    bin_indices_list = []

    hist, bin_edges = np.histogram(rel_dom_times, weights=dom_charges,
                                   bins=config['time_bins'])
    for i, charge in enumerate(hist):
        if charge != 0:
            bin_values_list.append(charge)
            bin_indices_list.append(i)

    return bin_values_list, bin_indices_list


def charge_bins_and_times(dom_charges, rel_dom_times, global_time_offset,
                          local_time_offset, config, *args, **kwargs):
    """Histogram charge in time bins as given by config['time_bins'] as well as
    the time of the first pulse and the total time offset.

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """
    bin_values_list = []
    bin_indices_list = []

    total_time_offset = local_time_offset + global_time_offset
    bin_values_list.append(rel_dom_times[0] + total_time_offset)
    bin_indices_list.append(0)
    bin_values_list.append(total_time_offset)
    bin_indices_list.append(1)

    hist, bin_edges = np.histogram(rel_dom_times, weights=dom_charges,
                                   bins=config['time_bins'])
    for i, charge in enumerate(hist):
        if charge != 0:
            bin_values_list.append(charge)
            bin_indices_list.append(i + 2)

    return bin_values_list, bin_indices_list


def autoencoder(dom_charges, rel_dom_times, global_time_offset,
                local_time_offset, config, *args, **kwargs):
    """Encodes pulse data with an autoencoder.

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """
    total_time_offset = local_time_offset + global_time_offset

    bin_values_list, bin_indices_list = autoencoder.get_encoded_data(
                        config['autoencoder'],
                        config['autoencoder_name'],
                        dom_times=rel_dom_times,
                        dom_charges=dom_charges,
                        bins=config['time_bins'],
                        autoencoder_settings=config['autoencoder_settings'],
                        time_offset=total_time_offset)
    return bin_values_list, bin_indices_list


def charge_weighted_time_quantiles(dom_charges, rel_dom_times,
                                   global_time_offset, local_time_offset,
                                   config, *args, **kwargs):
    """Calculate charge weighted time quantiles for the quantiles specified
    in config['time_quantiles'].

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """
    bin_values_list = []
    bin_indices_list = []

    # add total charge at DOM
    total_dom_charge = np.sum(dom_charges)
    bin_values_list.append(total_dom_charge)
    bin_indices_list.append(0)

    # compute cumulative sum
    cum_charge = np.cumsum(dom_charges) / total_dom_charge

    # small constant:
    epsilon = 1e-6

    # add time quantiles
    for i, q in enumerate(config['time_quantiles']):

        # get time of pulse at which the cumulative charge is
        # first >= q:
        mask = cum_charge >= q - epsilon
        q_value = rel_dom_times[mask][0]

        bin_values_list.append(q_value)
        bin_indices_list.append(i+1)

    return bin_values_list, bin_indices_list


def pulse_summmary_clipped(dom_charges, rel_dom_times, global_time_offset,
                           local_time_offset, config, *args, **kwargs):
    """Calculate summary values from clipped pulses.

    These include:
        1.) Total DOM charge
        2.) Charge within 500ns of first pulse.
        3.) Charge within 100ns of first pulse.
        4.) Relative time of first pulse. (relative to total time offset)
        5.) Charge weighted quantile with q = 0.2
        6.) Charge weighted quantile with q = 0.5 (median)
        7.) Relative time of last pulse. (relative to total time offset)
        8.) Charge weighted mean pulse arrival time
        9.) Charge weighted std of pulse arrival time

    Parameters
    ----------
    dom_charges : numpy.ndarray
        The charges of the pulses measured at the DOM.
    rel_dom_times : numpy.ndarray
        The relative times of the pulses measured at the DOM.
    global_time_offset : float
        The global time offset which is the same for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    local_time_offset : float
        The local time offset which is different for all DOMs.
        The rel_dom_times are relative to the sum of local and global
        time offset.
    config : dict
        A dictionary that contains all configuration settings.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    list
        Values of non-zero data bins.
    list
        Bin indices to which the returned values belong to.
    """
    # --------------------------------------
    # clip pulses outside of [-5000, 14000]
    # --------------------------------------
    clip_mask = rel_dom_times >= -5000
    clip_mask = np.logical_and(clip_mask, rel_dom_times <= 14000)
    rel_dom_times = rel_dom_times[clip_mask]
    dom_charges = dom_charges[clip_mask]
    # --------------------------------------

    dom_charge_sum = sum(dom_charges)
    rel_dom_times_first = rel_dom_times[0]
    rel_dom_times_last = rel_dom_times[-1]

    charge_weighted_mean_time = np.average(rel_dom_times, weights=dom_charges)
    charge_weighted_std_time = weighted_std(rel_dom_times, weights=dom_charges)
    charge_weighted_quantile20_time = weighted_quantile(
                            rel_dom_times, weights=dom_charges, quantile=0.2)
    charge_weighted_quantile50_time = weighted_quantile(
                            rel_dom_times, weights=dom_charges, quantile=0.5)

    mask_100ns_interval = rel_dom_times - rel_dom_times_first < 100
    mask_500ns_interval = rel_dom_times - rel_dom_times_first < 500

    dom_charge_sum_100ns = np.sum(dom_charges[mask_100ns_interval])
    dom_charge_sum_500ns = np.sum(dom_charges[mask_500ns_interval])

    bin_values_list = [dom_charge_sum,
                       dom_charge_sum_500ns,
                       dom_charge_sum_100ns,
                       rel_dom_times_first,
                       charge_weighted_quantile20_time,
                       charge_weighted_quantile50_time,
                       rel_dom_times_last,
                       charge_weighted_mean_time,
                       charge_weighted_std_time,
                       ]
    bin_indices_list = range(len(bin_values_list))
    return bin_values_list, bin_indices_list
