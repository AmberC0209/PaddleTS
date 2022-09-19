# !/usr/bin/env python3
# -*- coding:utf-8 -*-

from paddlets import TSDataset
from paddlets.logger import raise_if

import numpy as np
from typing import List, Dict, Tuple, Optional


class MLDataset(object):
    """
    Machine learning Dataset.

    1> The in_chunk_len can be divided into several case: in_chunk_len = 0 indicates that the ML model has been
        processed by lag transform; in_chunk_len > 0 indicates that the ML model has NOT been processed by lag
        transform; in_chunk_len < 0 is NOT allowed.

    2> The unused (known / observed) columns should be deleted before the dataset passed in.

    3> The default time_window assumes each sample contains X (i.e. in_chunk), skip_chunk, and
    Y (i.e. out_chunk).

    4> If caller explicitly passes time_window parameter in, and time_window upper bound is larger than
    len(TSDataset._target) - 1, it means that each built sample will only contain X (i.e. in_chunk), but
    will not contain skip_chunk or Y (i.e. out_chunk). This occurs only if caller wants to build a sample
    used for prediction, as only in this scenario the Y (i.e. out_chunk) is not required.

    Args:
        rawdataset(TSDataset): TSDataset to build.
        in_chunk_len(int): The length of past target time series chunk for a single sample.
        out_chunk_len(int): The length of future target time series chunk for a single sample.
        skip_chunk_len(int): The length of time series chunk between past target and future target for a single sample.
             The skip chunk are neither used as feature (i.e. X) nor label (i.e. Y) for a single sample.
        sampling_stride(int, optional): Time steps to stride over the i-th sample and (i+1)-th sample.
        time_window(Tuple, optional): A two-element-tuple-shaped time window that allows adapter to build samples.
                time_window[0] refers to the window lower bound, while time_window[1] refers to the window upper bound.
                Each element in the left-closed-and-right-closed interval refers to the TAIL index of each sample.

    Attributes:
        _rawdataset(TSDataset) Tsdataset to build.
        _target_in_chunk_len(int): The length of past target time series chunk for a single sample.
        _target_out_chunk_len(int): The length of future target time series chunk for a single sample.
        _target_skip_chunk_len(int): The length of time series chunk between past target and future target for a single
            sample. The skip chunk are neither used as feature (i.e. X) nor label (i.e. Y) for a single sample.
        _known_cov_chunk_len(int): The length of known covariates time series chunk for a single sample.
        _observed_cov_chunk_len(int): The length of observed covariates time series chunk for a single sample.
        _sampling_stride(int): Time steps to stride over the i-th sample and (i+1)-th sample.
        _time_window(Tuple, optional): A two-element-tuple-shaped time window that allows adapter to build samples.
            time_window[0] refers to the window lower bound, while time_window[1] refers to the window upper bound.
            Each element in the left-closed-and-right-closed interval refers to the TAIL index of each sample.
        _samples(List[Dict[str, np.ndarray]]): The built samples.

    Examples:
        .. code-block:: python

            # 1) in_chunk_len examples
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4]
            skip_chunk_len = 0
            out_chunk_len = 1

            # 1.1) If in_chunk_len = 1, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)

            # 1.2) If in_chunk_len = 2, sample[0]:
            # X -> skip_chunk -> Y
            # (0, 1) -> () -> (2)

            # 1.3) If in_chunk_len = 3, sample[0]:
            # X -> skip_chunk -> Y
            # (0, 1, 2) -> () -> (3)

        .. code-block:: python

            # 2) out_chunk_len examples
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4]
            in_chunk_len = 1
            skip_chunk_len = 0

            # 2.1) If out_chunk_len = 1, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)

            # 2.2) If out_chunk_len = 2, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1, 2)

            # 2.3) If out_chunk_len = 3, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1, 2, 3)

        .. code-block:: python

            # 3) skip_chunk_len examples
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4]
            in_chunk_len = 1
            out_chunk_len = 1

            # 3.1) If skip_chunk_len = 0, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)

            # 3.2) If skip_chunk_len = 1, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> (1) -> (2)

            # 3.3) If skip_chunk_len = 2, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> (1, 2) -> (3)

            # 3.4) If skip_chunk_len = 3, sample[0]:
            # X -> skip_chunk -> Y
            # (0) -> (1, 2, 3) -> (4)

        .. code-block:: python

            # 4) sampling_stride examples
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4]
            in_chunk_len = 1
            skip_chunk_len = 0
            out_chunk_len = 1

            # 4.1) If sampling_stride = 1, samples:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)
            # (1) -> () -> (2)
            # (2) -> () -> (3)
            # (3) -> () -> (4)

            # 4.2) If sampling_stride = 2, samples:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)
            # (2) -> () -> (3)

            # 4.3) If sampling_stride = 3, samples:
            # X -> skip_chunk -> Y
            # (0) -> () -> (1)
            # (3) -> () -> (4)

        .. code-block:: python

            # 5) time_window examples:
            # 5.1) The default time_window calculation formula is as follows:
            # time_window[0] = 0 + in_chunk_len + skip_chunk_len + (out_chunk_len - 1)
            # time_window[1] = max_target_idx
            #
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            in_chunk_len = 4
            skip_chunk_len = 3
            out_chunk_len = 2
            sampling_stride = 1

            # The following equation holds:
            max_target_idx = tsdataset.target[-1] = 10

            # The default time_window is calculated as follows:
            time_window[0] = 0 + 2 + 3 + (4 - 1) = 5 + 3 = 8
            time_window[1] = max_target_idx = 10
            time_window = (8, 10)

            # 3 samples will be built in total:
            X -> Y
            (0, 1, 2, 3) -> (7, 8)
            (1, 2, 3, 4) -> (8, 9)
            (2, 3, 4, 5) -> (9, 10)


            # 5.2) Each element in time_window refers to the TAIL index of each sample, but NOT the HEAD index.
            # The following two scenarios shows how to pass in the expected time_window parameter to build samples.
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            in_chunk_len = 4
            skip_chunk_len = 3
            out_chunk_len = 2

            # Scenario 5.2.1 - Suppose the following training samples are expected to be built:
            # X -> Y
            # (0, 1, 2, 3) -> (7, 8)
            # (1, 2, 3, 4) -> (8, 9)
            # (2, 3, 4, 5) -> (9, 10)

            # The 1st sample's tail index is 8
            # The 2nd sample's tail index is 9
            # The 3rd sample's tail index is 10

            # Thus, the time_window parameter should be as follows:
            time_window = (8, 10)

            # All other time_window showing up as follows are NOT correct:
            time_window = (0, 2)
            time_window = (0, 10)

            # Scenario 5.2.2 - Suppose the following predict sample is expected to be built:
            # X -> Y
            # (7, 8, 9, 10) -> (14, 15)

            # The first (i.e. the last) sample's tail index is 15;

            # Thus, the time_window parameter should be as follows:
            time_window = (15, 15)

            # 5.3) The calculation formula of the max allowed time_window upper bound is as follows:
            # time_window[1] <= len(tsdataset.target) - 1 + skip_chunk_len + out_chunk_len
            # The reason is that the built paddle.io.Dataset is used for a single call of :func: `model.predict`, as
            # it only allow for a single predict sample, any time_window upper bound larger than a single predict
            # sample's TAIL index will not be allowed because there is not enough target time series to build past
            # target time series chunk.
            #
            # Given:
            tsdataset.target = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            in_chunk_len = 4
            skip_chunk_len = 3
            out_chunk_len = 2

            # For a single :func:`model.predict` call:
            X = in_chunk = (7, 8, 9, 10)

            # max allowed time_window[1] is calculated as follows:
            time_window[1] <= len(tsdataset) - 1 + skip_chunk_len + out_chunk_len = 11 - 1 + 3 + 2 = 15

            # Note that time_window[1] (i.e. 15) is larger than the max_target_idx (i.e. 10), but this time_window
            # upper bound is still valid, because predict sample does not need skip_chunk (i.e.  [11, 12, 13]) or
            # out_chunk (i.e. [14, 15]).

            # Any values larger than 15 (i.e. 16) is invalid, because the existing target time series is NOT long
            # enough to build X for the prediction sample, see following example:
            # Given:
            time_window = (16, 16)

            # The calculated out_chunk = (15, 16)
            # The calculated skip_chunk = (12, 13, 14)

            # Thus, the in_chunk should be [8, 9, 10, 11]
            # However, the tail index of the calculated in_chunk 11 is beyond the max target time series
            # (i.e. tsdataset.target[-1] = 10), so current target time series cannot provide 11 to build this sample.
    """
    def __init__(
        self,
        rawdataset: TSDataset,
        in_chunk_len: int,
        out_chunk_len: int,
        skip_chunk_len: int,
        sampling_stride: int,
        time_window: Optional[Tuple] = None
    ):
        self._rawdataset = rawdataset
        self._target_in_chunk_len = in_chunk_len
        self._target_out_chunk_len = out_chunk_len
        self._target_skip_chunk_len = skip_chunk_len
        self._known_cov_chunk_len = self._target_in_chunk_len + self._target_out_chunk_len
        self._observed_cov_chunk_len = 1 if self._target_in_chunk_len == 0 else self._target_in_chunk_len
        self._sampling_stride = sampling_stride
        self._time_window = time_window

        raise_if(rawdataset is None, "TSDataset must not be None.")
        raise_if(rawdataset.get_target() is None, "TSDataset target Timeseries must not be None.")
        raise_if(len(rawdataset.get_target().time_index) < 1, "TSDataset target Timeseries length must >= 1.")
        raise_if(
            in_chunk_len < 0,
            "in_chunk_len must be non-negative integer, but %s is actually provided." % in_chunk_len
        )
        raise_if(
            skip_chunk_len < 0,
            "skip_chunk_len must be non-negative integer, but %s is actually provided." % skip_chunk_len
        )
        raise_if(
            out_chunk_len <= 0,
            "out_chunk_len must be positive integer, but %s is actually provided." % out_chunk_len
        )
        raise_if(
            sampling_stride <= 0,
            "sampling_stride must be positive integer, but %s is actually provided." % sampling_stride
        )

        # Compute a default time_window if caller does not provide it.
        if self._time_window is None:
            # The default time_window assumes each sample contains both X, skip_chunk and Y, thus requires the length
            # of the target timeseries must be greater than or equal to the sum of X, skip_chunk and Y.
            raise_if(
                len(rawdataset.get_target().time_index) < max(1, in_chunk_len) + skip_chunk_len + out_chunk_len,
                """If time_window is not specified, TSDataset target timeseries length must be equal or larger than 
                the sum of max(1, in_chunk_len), skip_chunk_len and out_chunk_len. 
                Current in_chunk_len = %s, skip_chunk_len = %s, out_chunk_len = %s.""" %
                (in_chunk_len, skip_chunk_len, out_chunk_len)
            )
            default_min_window = self._compute_min_allowed_window()
            default_max_window = len(rawdataset.get_target().time_index) - 1
            self._time_window = (default_min_window, default_max_window)

        min_allowed_window = self._compute_min_allowed_window()
        raise_if(
            self._time_window[0] < min_allowed_window,
            "time_window lower bound must be equal or larger than %s" % min_allowed_window
        )

        max_allowed_window = len(rawdataset.get_target().data) - 1 + skip_chunk_len + out_chunk_len
        raise_if(
            self._time_window[1] > max_allowed_window,
            "time window upper bound must be equal or smaller than %s" % max_allowed_window
        )

        # Validates input TSDataset, raises if the passed data is invalid.
        # Firstly, valid target timeseries.
        max_target_idx = len(rawdataset.get_target().time_index) - 1
        max_target_timestamp = rawdataset.get_target().time_index[max_target_idx]
        if self._time_window[1] > max_target_idx:
            # This `if` statement indicates that caller is building a sample only containing feature (i.e. X),
            # but NOT containing skip_chunk or label (i.e. Y).
            # Thus, as long as the target is long enough to build the X of a sample, it can be treated as valid.
            min_allowed_target_len = max(1, in_chunk_len)
        else:
            # This `else` statement indicates that caller is building a sample both containing feature (i.e. X),
            # skip_chunk and label (i.e. Y).
            # Thus, as long as the target is long enough to build a (X + skip + Y) sample, it can be treated as valid.
            min_allowed_target_len = max(1, in_chunk_len) + skip_chunk_len + out_chunk_len
        raise_if(
            len(rawdataset.get_target().time_index) < min_allowed_target_len,
            """Given TSDataset target timeseries length is too short to build even one sample, 
            actual time_window: (%s, %s), actual target timeseries length: %s, min allowed sample length: %s. 
            If time_window[1] > max target index, sample length includes Y but not includes X or skip chunk, 
            else if time_window[1] <= max target index, sample length includes both X and skip chunk and Y.""" %
            (
                self._time_window[0],
                self._time_window[1],
                len(rawdataset.get_target().time_index),
                min_allowed_target_len
            )
        )

        # Secondly, validates known_cov timeseries.
        target_timeindex = rawdataset.get_target().time_index
        if rawdataset.get_known_cov() is not None:
            known_timeindex = rawdataset.get_known_cov().time_index
            if self._time_window[1] > max_target_idx:
                # (Note that the following statement uses `w` as the abbreviation of `_time_window`).
                # This `if` statement indicates a scenario where the built sample only contains X, but NOT contains Y.
                # Known that the max known cov timestamp must be greater than or equal to the timestamp which
                # w[1] pointed to.
                # In the meantime, as in this case w[1] > max target index, thus, the known cov timeseries must be
                # longer than the target timeseries, refers to the following example compute process:
                # Known that the `TSDataset` requires that target_timeseries and known_timeseries must have same freq,
                # given:
                # target_timeindex = target_timeseries.time_index = [8:00, 9:00, 10:00]
                # known_timeindex = known_timeseries.time_index = [7:00, 8:00, 9:00, 10:00, 11:00]
                # in_chunk_len = 1
                # skip_chunk_len = 0
                # out_chunk_len = 2
                # w = [4, 4]
                # Thus, the timestamp of the predicted chunk can be calculated to be equal to [11:00, 12:00],
                # thus, requires max timestamp of known_timeseries must be equal or larger than 12:00.
                # Below is the calculation process based on the above mock data:
                # Firstly, get:
                # max_target_idx = len(target_timeindex) - 1 = 2, thus, max_target_timestamp = 10:00
                # Secondly, compute the index position of max_target_timestamp in known_timeindex, i.e.
                # max_target_timestamp_idx_in_known = known_timeindex.get_loc(10:00) = 3.
                # Thirdly, compute the extra required time steps to build features (i.e. X) of the current sample:
                # exceed_time_steps_in_known = time_window[1] - max_target_idx = 4 - 2 = 2
                # So far, known that max_target_timestamp_idx_in_known = 3, exceed_time_steps_in_known = 2, thus:
                # needs to ensure that the following equation holds:
                # len(known_timeindex[max_target_timestamp_idx_in_known:]) > exceed_time_steps_in_known
                # However, according the previously computed result,
                # len(known_timeindex[max_target_timestamp_idx_in_known:]) = len(known_timeindex[3:]) = 2 which is
                # NOT larger than exceed_time_steps_in_known (i.e. 2), thus, the above equation does NOT hold,
                # thus causes the current known cov timeseries failed to build known_cov_chunk features for the sample.
                # END.
                raise_if(
                    known_timeindex[-1] < max_target_timestamp,
                    """If time_window upper bound is larger than len(target timeseries) - 1, 
                    known_cov max timestamp must be equal or larger than target max timestamp. 
                    Current time_window: (%s, %s), len(target timeseries) - 1 = %s, 
                    known_cov max timestamp = %s, target max timestamp = %s""" %
                    (
                        self._time_window[0],
                        self._time_window[1],
                        len(target_timeindex) - 1,
                        known_timeindex[-1],
                        max_target_timestamp
                    )
                )
                # Compute the index position of the max_target_timestamp in known_timeindex.
                idx = known_timeindex.get_loc(max_target_timestamp)
                # Compute the extra time steps to build known_cov features of the current sample.
                exceeded_time_steps = self._time_window[1] - max_target_idx
                raise_if(
                    # Tips: the expression `len(a[x:] ) > b` and `len(a[x+1:]) >= b` have the same effect, however
                    # `a[x+1:]` requires extra `out of upper bound` check for `a`, which causes more code and less
                    # robustness, thus use `a[x:]` approach here.
                    len(known_timeindex[idx:]) <= exceeded_time_steps,
                    """known_cov length is too short to build known_cov chunk feature. 
                    It needs at least %s extra Timestamps after known_timeseries.time_index[%s:]""" %
                    (exceeded_time_steps, idx)
                )
            else:
                # This `else` indicates that the built samples contain both X, skip_chunk and Y.
                # Let `upper_window_timestamp` be the timestamp which time_window[1] pointed to, the following equation
                # needs to be held:
                # known_timeindex[-1] >= upper_window_timestamp
                # Otherwise the target timeseries will be too short to build the samples within the range specified by
                # time_window.
                upper_window_timestamp = target_timeindex[self._time_window[1]]
                raise_if(
                    known_timeindex[-1] < upper_window_timestamp,
                    """max known_cov timestamp must be equal or larger than time_window upper bound timestamp, 
                    actual max known_cov timestamp: %s, actual time_window upper bound timestamp: %s.""" %
                    (known_timeindex[-1], upper_window_timestamp)
                )

        # Thirdly(Lastly), validates observed_cov timeseries
        if rawdataset.get_observed_cov() is not None:
            observed_timeindex = rawdataset.get_observed_cov().time_index
            # Known that max observed_cov timestamp no need to be larger than the max target timeindex.
            # Thus exceed_time_steps is no need to be computed here, which is different from known_cov.
            if self._time_window[1] > max_target_idx:
                # This `if` indicates that it is a prediction scenario where the built sample only contains X, but NOT
                # contains skip_chunk or Y.
                # Thus, the observed_cov only needs to ensure that its max timestamp is always >= max target timestamp.
                raise_if(
                    observed_timeindex[-1] < max_target_timestamp,
                    """if time_window upper bound is larger than max target, the max observed timestamp must 
                    be equal or larger than max target timestamp so that observed timeseries is long enough to build 
                    samples. Actual max observed timestamp: %s, max target timestamp: %s, time_window: (%s, %s)""" %
                    (
                        observed_timeindex[-1],
                        max_target_timestamp,
                        self._time_window[1],
                        self._time_window[1]
                    )
                )
            else:
                # This `else` indicates that this is for fit scenario where the built samples contain both X,
                # skip_chunk and Y.
                last_sample_past_target_tail = self._time_window[1] - \
                    self._target_skip_chunk_len - \
                    self._target_out_chunk_len
                last_sample_past_target_tail_timestamp = target_timeindex[last_sample_past_target_tail]
                # Observed cov does not need to provide `future` features, thus only need to ensure that the max
                # observed cov timestamp is large enough to build the `observed` feature of the last sample, i.e. the
                # following equation needs to be held:
                raise_if(
                    observed_timeindex[-1] < last_sample_past_target_tail_timestamp,
                    """if time_window upper bound is equal or smaller than max target, the max observed timestamp must 
                    be equal or larger than timestamp the time_window upper bound pointed to, so that 
                    observed timeseries is long enough to build samples. Actual max observed timestamp: %s, 
                    max target timestamp: %s, time_window: (%s, %s)""" %
                    (
                        observed_timeindex[-1],
                        max_target_timestamp,
                        self._time_window[1],
                        self._time_window[1]
                    )
                )

        self._samples = self._build_samples()

    def __len__(self):
        return len(self._samples)

    def __getitem__(self, idx: int) -> Dict[str, np.ndarray]:
        # TODO
        # Currently the implementation build full data in the construct method, which will probably cause performance
        # waste if the number of the built full-data samples are much larger than the number model actually needed
        # while fitting.
        # Consider optimize this scenario later.
        return self._samples[idx]

    def _build_samples(self) -> List[Dict[str, np.ndarray]]:
        """
        Internal method, builds samples.

        Returns:
            List[Dict[str, np.ndarray]]: A list of samples.

        Examples:
            1) lag scenario (TSDataset has been processed by lag transform):
            Given:
            in_chunk_len = 0 (in_chunk_len = 0 indicates that this is lag scenario.)
            skip_chunk_len = 1
            out_chunk_len = 2
            sampling_stride = 1
            time_window = (2, 5)
            rawdataset = {
                target: [
                    [0, 0],
                    [1, 10],
                    [2, 20],
                    [3, 30],
                    [4, 40],
                    [5, 50],
                    [6, 60],
                    [7, 70]
                ],
                known_cov: [
                    [0, 0, 0],
                    [10, 100, 1000],
                    [20, 200, 2000],
                    [30, 300, 3000],
                    [40, 400, 4000],
                    [50, 500, 5000],
                    [60, 600, 6000],
                    [70, 700, 7000],
                    [80, 800, 8000]
                ],
                # Note that features originally in target timeseries will be processed and added to observed_cov.
                # For example, the following 2nd and 3rd columns are originally lying in target time series, and then
                # being processed by lag-transform and added to observed_cov.
                observed_cov: [
                    [0, NaN, NaN],
                    [-1, 0, 0],
                    [-2, 1, 10],
                    [-3, 2, 20],
                    [-4, 3, 30],
                    [-5, 4, 40],
                    [-6, 5, 50],
                    [-7, 6, 60]
                ],
                static_cov: {"f": 1, "g": 2}
            }

            The built samples:
            np.ndarray = [
                # sample[0]
                {
                    # past_target will always be empty matrix, which is what `in_chunk_len = 0` means.
                    "past_target": np.array(shape=(0, 0)),

                    # future target time series chunk (i.e. Y), totally contains _target_out_chunk_len time steps.
                    # Note that skip_chunk_len = 1 time steps are skipped, so [1, 10] are not showing up here.
                    "future_target": [
                        [2, 20],
                        [3, 30]
                    ],
                    known covariates time series chunk, totally contains _known_cov_chunk_len time steps.
                    "known_cov": [
                        [20, 200, 2000]，
                        [30, 300, 3000]
                    ],
                    # observed covariates time series chunk, totally contains _observed_cov_chunk_len time steps.
                    "observed_cov": [
                        [0, NaN, NaN]
                    ]
                },

                # sample[1]
                {
                    "past_target": np.array(shape=(0, 0)),
                    "future_target": [
                        [3, 30],
                        [4, 40]
                    ],
                    "known_cov": [
                        [30, 300, 3000],
                        [40, 400, 4000]
                    ],
                    "observed_cov": [
                        [-1, 0, 0]
                    ]
                },

                # sample[2]
                {
                    "past_target": np.array(shape=(0, 0)),
                    "future_target": [
                        [4, 40],
                        [5, 50]
                    ],
                    "known_cov": [
                        [40, 400, 4000],
                        [50, 500, 5000]
                    ],
                    "observed_cov": [
                        [-2, 1, 10]
                    ]
                },

                # sample[3]
                {
                    "past_target": np.array(shape=(0, 0)),
                    "future_target": [
                        [5, 50],
                        [6, 60]
                    ],
                    "known_cov": [
                        [50, 500, 5000],
                        [60, 600, 6000]
                    ],
                    "observed_cov": [
                        [-3, 2, 20]
                    ]
                },

                sample[4] (i.e. last sample, future_target tail index = 7 reaches time_window upper bound)
                {
                    "past_target": np.array(shape=(0, 0)),
                    "future_target": [
                        [6, 60],
                        [7, 70]
                    ],
                    "known_cov": [
                        [60, 600, 6000],
                        [70, 700, 7000]
                    ],
                    "observed_cov": [
                        [-4, 3, 30]
                    ]
                }
            ]

            2) non-lag scenario (TSDataset has NOT been processed by lag transform):
            Given:
            in_chunk_len = 2 (in_chunk_len > 0 indicates that this is NOT lag scenario.)
            skip_chunk_len = 1
            out_chunk_len = 2
            sampling_stride = 1
            time_window = (4, 7)
            rawdataset = {
                target: [
                    [0, 0],
                    [1, 10],
                    [2, 20],
                    [3, 30],
                    [4, 40],
                    [5, 50],
                    [6, 60],
                    [7, 70]
                ],
                known_cov: [
                    [0, 0, 0],
                    [10, 100, 1000],
                    [20, 200, 2000],
                    [30, 300, 3000],
                    [40, 400, 4000],
                    [50, 500, 5000],
                    [60, 600, 6000],
                    [70, 700, 7000],
                    [80, 800, 8000]
                ],
                observed_cov: [
                    [0],
                    [-1],
                    [-2],
                    [-3],
                    [-4],
                    [-5],
                    [-6],
                    [-7]
                ],
                static_cov: {"f": 1, "g": 2}
            }

            Built samples:
            np.ndarray = [
                # sample[0]
                {
                    # past target time series chunk, totally contains _target_in_chunk_len time steps.
                    "past_target": [
                        [0, 0],
                        [1, 10]
                    ],
                    # future target time series chunk (i.e. Y), totally contains _target_out_chunk_len time steps.
                    # Note that skip_chunk_len = 1 time steps are skipped between past_target and future_target.
                    "future_target": [
                        [3, 30],
                        [4, 40]
                    ],
                    # known covariates time series chunk, totally contains _known_cov_chunk_len time steps.
                    # Note that skip_chunk_len = 1 time steps are skipped between past_target and future_target.
                    "known_cov": [
                        [0, 0, 0],
                        [10, 100, 1000],
                        # Note that skip_chunk [20, 200, 2000] is skipped between [10, 100, 1000] and [30, 300, 3000].
                        [30, 300, 3000],
                        [40, 400, 4000]
                    ],
                    # observed covariates time series chunk, totally contains _observed_cov_chunk_len time steps.
                    "observed_cov": [
                        [0],
                        [-1]
                    ]
                },
                # sample[1]
                {
                    "past_target": [
                        [1, 10]
                        [2, 20]
                    ],
                    "future_target": [
                        [4, 40],
                        [5, 50]
                    ],
                    "known_cov": [
                        [10, 100, 1000],
                        [20, 200, 2000],
                        [40, 400, 4000],
                        [50, 500, 5000]
                    ],
                    "observed_cov": [
                        [-1],
                        [-2]
                    ]
                },
                # sample[2]
                {
                    "past_target": [
                        [2, 30]
                        [3, 30]
                    ],
                    "future_target": [
                        [5, 50],
                        [6, 60],
                    ],
                    "known_cov": [
                        [20, 200, 2000],
                        [30, 300, 3000],
                        [50, 500, 5000],
                        [60, 600, 6000]
                    ],
                    "observed_cov": [
                        [-2],
                        [-3]
                    ]
                },
                # sample[3] (i.e. last sample, future_target tail index = 7 reaches time_window upper bound)
                {
                    "past_target": [
                        [3, 30]
                        [4, 40]
                    ],
                    "future_target": [
                        [6, 60],
                        [7, 70]
                    ],
                    "known_cov": [
                        [30, 300, 3000],
                        [40, 400, 4000],
                        [60, 600, 6000],
                        [70, 700, 7000]
                    ],
                    "observed_cov": [
                        [-3],
                        [-4]
                    ]
                }
            ]
        """
        target_ts = self._rawdataset.get_target()
        target_ndarray = target_ts.to_numpy(copy=False)

        # Consider the case where covariates is None.
        # As it is not mandatory for the models to use the covariates as features, thus covariates are VALID to be None.
        known_cov_ts = self._rawdataset.get_known_cov()
        known_cov_ndarray = None
        if known_cov_ts is not None:
            known_cov_ndarray = known_cov_ts.to_numpy(copy=False)
        observed_cov_ts = self._rawdataset.get_observed_cov()
        observed_cov_ndarray = None
        if observed_cov_ts is not None:
            observed_cov_ndarray = observed_cov_ts.to_numpy(copy=False)

        samples = []
        # `future_target_tail` refers to the tail index of the future_target chunk for each sample.
        future_target_tail = self._time_window[0]
        # Because _time_window is left-closed-right-closed, thus using `<=` operator rather than `<`.
        while future_target_tail <= self._time_window[1]:
            sample = {"past_target": None, "future_target": None, "known_cov": None, "observed_cov": None}

            # Build future_target
            if future_target_tail > len(target_ts.time_index) - 1:
                # In this case, the built sample only contains  X, but not contains skip_chunk and Y, thus filled with
                # all zeros ndarray.
                sample["future_target"] = np.zeros(shape=(0, 0))
            else:
                # In this case, the built samples contain both X, skip_chunk and Y.
                sample["future_target"] = \
                    target_ndarray[future_target_tail - self._target_out_chunk_len + 1:future_target_tail + 1]

            # Build past_target
            past_target_tail = future_target_tail - self._target_out_chunk_len - self._target_skip_chunk_len
            if self._target_in_chunk_len == 0:
                # lag case.
                sample["past_target"] = np.zeros(shape=(0, 0))
            else:
                # not-lag case.
                sample["past_target"] = \
                    target_ndarray[past_target_tail - self._target_in_chunk_len + 1:past_target_tail + 1]

            # Build known_cov.
            # known_cov = left + right, where left = (in, skip), right = (skip, out).
            if known_cov_ts is not None:
                if future_target_tail > len(target_ts.time_index) - 1:
                    max_target_timestamp = target_ts.time_index[-1]
                    # compute the index position of max_target_timestamp in known_cov.
                    max_target_timestamp_idx_in_known = known_cov_ts.time_index.get_loc(max_target_timestamp)
                    known_cov_right_tail = max_target_timestamp_idx_in_known + \
                        self._target_skip_chunk_len + \
                        self._target_out_chunk_len
                else:
                    future_target_tail_timestamp = target_ts.time_index[future_target_tail]
                    known_cov_right_tail = known_cov_ts.time_index.get_loc(future_target_tail_timestamp)
                # right
                known_cov_right = \
                    known_cov_ndarray[known_cov_right_tail - self._target_out_chunk_len + 1:known_cov_right_tail + 1]
                # left
                known_cov_left_tail = known_cov_right_tail - self._target_out_chunk_len - self._target_skip_chunk_len
                known_cov_left = \
                    known_cov_ndarray[known_cov_left_tail - self._target_in_chunk_len + 1:known_cov_left_tail + 1]
                # known = right + left
                sample["known_cov"] = np.vstack((known_cov_left, known_cov_right))
            else:
                # If known_cov timeseries is None, to avoid the failure of the conversion from paddle.Dataset to
                # paddle.DataLoader, we need to fill the empty ndarray with np.NaN because paddle.Tensor cannot be
                # converted from a python built-in None object, but can be converted from a np.ndarray filled with NaN.
                sample["known_cov"] = np.zeros(shape=(0, 0))

            # Build observed_cov
            if observed_cov_ts is not None:
                past_target_tail_timestamp = target_ts.time_index[past_target_tail]
                observed_cov_tail = observed_cov_ts.time_index.get_loc(past_target_tail_timestamp)
                sample["observed_cov"] = \
                    observed_cov_ndarray[observed_cov_tail - self._observed_cov_chunk_len + 1:observed_cov_tail + 1]
            else:
                # If observed_cov timeseries is None, to avoid the failure of the conversion from paddle.Dataset to
                # paddle.DataLoader, we need to fill the empty ndarray with np.NaN because paddle.Tensor cannot be
                # converted from a python built-in None object, but can be converted from a np.ndarray filled with NaN.
                sample["observed_cov"] = np.zeros(shape=(0, 0))

            samples.append(sample)

            # The predefined `sampling_stride >= 1 assertion` in the construct method ensures that `infinite while loop`
            # will Not occur.
            future_target_tail += self._sampling_stride
        return samples

    def _compute_min_allowed_window(self) -> int:
        """
        Internal method, used for computing min allowed window lower bound based on given in/skip/out chunk len.

        Consider lag-transform case which will cause _target_in_chunk_len equal to zero, thus use
        max(1, self._target_in_chunk_len) to ensure that in_chunk will hold at least 1 time unit.

        Returns:
            int: Computed min allowed window lower bound.
        """
        return max(1, self._target_in_chunk_len) + self._target_skip_chunk_len + self._target_out_chunk_len - 1

    @property
    def samples(self):
        return self._samples
