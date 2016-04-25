import numpy as np
from allensdk.ephys.feature_extractor import EphysFeatureExtractor

ALIGN_CUT_WINDOW = np.array([ 0.002, 0.015 ])

def find_spikes_list(voltage_list, dt):
    out_idx = []
    out_v = []
    
    for v in voltage_list:
        idx, v = find_spikes(v, dt)
        out_idx.append(idx)
        out_v.append(v)

    return out_idx, out_v


def find_spikes(v, dt):
    v = v * 1e3 # convert V => mV
    t = np.arange(0, len(v)) * dt    
    i = np.zeros(t.shape)
    fx = EphysFeatureExtractor()

    fx.process_instance("", v, i ,t, 0, t[-1], "")
    feature_data = fx.feature_list[0].mean

    ids = np.array([ s["threshold_idx"] for s in feature_data["spikes"] ])
    vs = np.array([ s["threshold_v"] for s in feature_data["spikes"] ]) 

    vs /= 1e3 # mV => V

    return ids, vs


def align_and_cut_spikes(voltage_list, current_list, dt, spike_window = None):
    ''' This function aligns the spikes to some criteria and returns a current and voltage trace of 
    of the spike over a time window.  Also returns zero crossing,and threshold 
    in reference to the aligned spikes.
    '''
    if spike_window is None:
        spike_window = ALIGN_CUT_WINDOW

    spike_shapes = []
    current_shapes = []
    index_before_spike = int(spike_window[0] / dt)
    index_after_spike = int(spike_window[1] / dt)
    aligned_spike_ind = np.array([])
    spike_sweeps = []
    spikes_per_trace = np.array([])
    
    spike_ind_list, _ = find_spikes_list(voltage_list, dt)

    for jj, voltage_and_current_and_spike in enumerate(zip(voltage_list, current_list, spike_ind_list)):
        voltage, current, whole_trace_spike_ind = voltage_and_current_and_spike
        
        spikes_per_trace = np.append(spikes_per_trace, len(whole_trace_spike_ind))
        
        alignment_ind = whole_trace_spike_ind                        
        aligned_spike_ind = np.append(aligned_spike_ind, np.ones(len(whole_trace_spike_ind)) * index_before_spike)

        # print 'alignment_ind', alignment_ind
        spike_delimiters = [(ind - index_before_spike, ind + index_after_spike) for ind in alignment_ind]
        for d in spike_delimiters: 
            # this 'if' statement makes sure we don't cause a ValueError
            if min(d) > 0 and max(d) < len(voltage) - 1:
                spike_trace = voltage[d[0]:d[1]]
                current_trace = current[d[0]:d[1]]
                spike_shapes.append(spike_trace)
                current_shapes.append(current_trace)                  
                spike_sweeps.append(jj)

            
    # note: that depending on how things were aligned, all of one of the values will be the same.
    print "spikes_per_trace", spikes_per_trace
    temp = np.append(0, np.cumsum(spikes_per_trace))  
    print 'temp', temp 
    wave_index_of_first_spikes = [int(ii) for ii in list(temp[range(0, len(temp) - 1)])]         
    print "in cut spikes: wave_index_of_first_spikes ", wave_index_of_first_spikes

    return spike_shapes, current_shapes, aligned_spike_ind, wave_index_of_first_spikes, spike_sweeps
