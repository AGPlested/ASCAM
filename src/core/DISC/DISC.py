# All credit for the DISC algorithm belongs to the authors of
# White, D.S., Goldschen-Ohm, M.P., Goldsmith, R.H., Chanda, B. Top-down machine learning approach for high-throughput single-molecule analysis. Elife 2020, 9
# The code in this module is based on their paper and partly on their
# matlab implementation at commit af19eae on https://github.com/ChandaLab/DISC/

from .divisive_segmentation import divisive_segmentation
from .agglomerative_clustering import agglomorative_clustering_fit
from .viterbi import viterbi_path_from_data

def run_DISC(data, confidence_level=0.05, min_seg_length=3,
             min_cluster_size=3, IC_div_seg="BIC", IC_HAC="BIC",
             BIC_method="full"):
    """
    Input:
        data - observations to be idealized
        confidence_level - alpha value for t-test in change point detection
        min_seg_length - minimum segment length in change point detection
        min_cluster_size - minimum cluster size for k-mean clustering
        IC_div_seg - information criterion for divisive segmentation
        IC_HAC - information criterion for agglomerative clustering
    Returns:
        an idealization of the data to the most likely sequence as found
        by the DISC algorithm
    """

    # 1) Start with divisive segmentation.
    data_fit, _ = divisive_segmentation(
                                        data,
                                        confidence_level=confidence_level,
                                        min_seg_length=min_seg_length,
                                        min_cluster_size=min_cluster_size,
                                        information_criterion=IC_div_seg,
                                        BIC_method=BIC_method
                                        )

    # 2) Perform Hierarchical Agglomerative Clustering (HAC) by
    # consecutively merging those clusters with the smallest Ward distance
    # between them. Then select the fit with the optimal number of clusters
    # as measured by the given Information Criterion (IC)
    data_fit = agglomorative_clustering_fit(data, data_fit, IC=IC_HAC)
    # At this point we could in the future include logic to return a
    # specific number of states (≤number of states found by divisive
    # segmentation, or multiple fits.

    # 3) Run Viterbi algorithm to find best fit to the given number of
    # states and their amplitudes.
    # Use empirical distribution of states as initial distribution for the
    # Viterbi algorithm. Compute best fit normal distribution for
    # emission matrix approximation.
    return viterbi_path_from_data(data, data_fit)
