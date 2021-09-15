import gzip
import logging
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import multiprocessing as mp
from abc import abstractmethod, ABC
from collections import OrderedDict
from interestingness_xdrl import InteractionDataPoint
from interestingness_xdrl.analysis.config import AnalysisConfiguration
from interestingness_xdrl.util.plot import format_and_save_plot, distinct_colors, TITLE_FONT_SIZE

__author__ = 'Pedro Sequeira'
__email__ = 'pedro.sequeira@sri.com'

TIME_FIG_HEIGHT = 6
TIME_FIG_WIDTH = 30
MAX_ELEM_COLOR = 'tab:red'
MIN_ELEM_COLOR = 'tab:green'
MARKER_SIZE = 7

EPISODE_STR = 'Episode'
TIME_STEP_STR = 'Timestep'


class AnalysisBase(ABC):
    """
    Represents the base class for analysis objects. Analyses extract useful information from the agent's history of
    interaction with its environment as provided by an interaction dataset. Typically, analyses will identify
    interestingness elements, i.e., situations that may be interesting to help explain an agent's behavior and aptitude
    in some task, both in terms of its capabilities and limitations. Each extracted element denotes a situation, e.g.,
    a specific simulation timestep, relevant according to different criteria.
    """

    def __init__(self, data, analysis_config, img_fmt):
        """
        Creates a new analysis.
        :param list[InteractionDataPoint] data: the interaction data collected to be analyzed.
        :param AnalysisConfiguration analysis_config: the analysis configuration containing the necessary parameters.
        :param str img_fmt: the format of the images to be saved.
        """
        self.data = data
        self.config = analysis_config
        self.img_fmt = img_fmt

    @abstractmethod
    def analyze(self, output_dir):
        """
        Analyzes the agent's history of interaction with its environment according to some criterion and collects
        interestingness elements relevant to that interaction.
        Also saves a report containing the relevant interestingness elements identified (in the form of tables, plots,
        analysis pickle film etc).
        :param str output_dir: the path to the directory in which to save the analysis report.
        :return:
        """
        pass

    @abstractmethod
    def get_element_time(self, t):
        """
        Gets the name of the interestingness element identified by this analysis at the given simulation timestep
        and the associated interestingness value.
        :param int t: the simulation timestep in which to identify interestingness elements.
        :rtype: tuple[str, float]
        :return: the names and value of the interestingness elements generated by this analysis at the given timestep.
        """
        pass

    @abstractmethod
    def get_element_datapoint(self, datapoint):
        """
        Analyzes a single interaction datapoint (as opposed to the whole history) and gets the name of the
        interestingness element identified therein and the associated interestingness value.
        :param InteractionDataPoint datapoint: the interaction datapoint that we want to analyze.
        :rtype: tuple[str, float]
        :return: the name and value of the interestingness element generated by this analysis given the datapoint.
        """
        pass

    def save(self, file_path):
        """
        Saves a Gzipped binary file representing this object.
        :param str file_path: the path to the file in which to save this analysis.
        :return:
        """
        # avoids saving interaction data, saves only analysis data
        data = self.data
        self.data = None

        with gzip.open(file_path, 'wb') as file:
            pickle.dump(self, file, protocol=pickle.HIGHEST_PROTOCOL)

        self.data = data

    @classmethod
    def load(cls, file_path):
        """
        Loads an analysis object from the given binary file.
        :param str file_path: the path to the binary file from which to load an object.
        :rtype: AnalysisBase
        :return: the object stored in the file.
        """
        with gzip.open(file_path, 'rb') as file:
            return pickle.load(file)

    def _get_mp_pool(self):
        """
        Creates a multiprocess pool according to the number of processes on the config file.
        Utility method for parallel processing of analyses.
        :rtype: mp.pool.Pool
        :return: a new multiprocess pool.
        """
        self.config.num_processes = -1
        pool = mp.Pool(self.config.num_processes if self.config.num_processes > 1 else None)
        logging.info('Set number of processes to {}'.format(
            self.config.num_processes if self.config.num_processes > 1 else mp.cpu_count()))
        return pool

    def _plot_elements(self, data, above_outliers, below_outliers,
                       high_limit, low_limit, output_img,
                       high_label, low_label, title, y_label):

        plt.figure(figsize=(TIME_FIG_WIDTH, TIME_FIG_HEIGHT))
        ax = plt.gca()

        # plots data
        ax.plot(data, label=y_label)

        # plots thresholds
        if not np.isnan(high_limit):
            ax.axhline(y=high_limit, label=high_label, c=MAX_ELEM_COLOR, ls='--')
        if not np.isnan(low_limit):
            ax.axhline(y=low_limit, label=low_label, c=MIN_ELEM_COLOR, ls='--')
        ax.axhline(y=np.mean(data), label='Overall mean', c='tab:blue', ls='--')

        # add episode breaks
        ep_breaks = np.where([datapoint.new_episode for datapoint in self.data])[0]
        for ep in ep_breaks:
            ax.axvline(x=ep, c='black', linewidth=0.2)

        # plot outliers
        high_means = [data[t] for t in above_outliers]
        plt.scatter(above_outliers, high_means, marker='o', s=MARKER_SIZE, c=MAX_ELEM_COLOR, zorder=100)
        low_means = [data[t] for t in below_outliers]
        plt.scatter(below_outliers, low_means, marker='o', s=MARKER_SIZE, c=MIN_ELEM_COLOR, zorder=100)

        ax.set_xlim(0, len(self.data))
        format_and_save_plot(ax, title, output_img, 'Timesteps', y_label)

    def _plot_elements_sp(self, data, high_limit, low_limit, output_img,
                          high_label, low_label, title, y_label, eps_per_plot=10):

        # split data into episodes
        ep_breaks = np.where([datapoint.new_episode for datapoint in self.data])[0].tolist()
        ep_breaks.remove(0)
        eps_data = np.split(data, ep_breaks)

        # create subplots
        plot_ep_splits = np.arange(0, len(eps_data), eps_per_plot)
        for ep_idx in plot_ep_splits:
            # creates figure and subplots
            plot_eps_data = eps_data[ep_idx:min(ep_idx + eps_per_plot, len(eps_data))]
            width_ratios = np.array([len(ep_data) for ep_data in plot_eps_data])
            width_ratios = width_ratios / width_ratios.sum()
            fig, axs = plt.subplots(1, len(plot_eps_data), sharey=True,
                                    figsize=(len(plot_eps_data) * TIME_FIG_WIDTH / 10, TIME_FIG_HEIGHT),
                                    gridspec_kw={'width_ratios': width_ratios})

            for ep, ax in enumerate(axs):
                # plots data
                ep_data = plot_eps_data[ep]
                ax.plot(ep_data, label=y_label)

                # plots thresholds
                if not np.isnan(high_limit):
                    ax.axhline(y=high_limit, c=MAX_ELEM_COLOR, ls='--')
                if not np.isnan(low_limit):
                    ax.axhline(y=low_limit, c=MIN_ELEM_COLOR, ls='--')
                ax.axhline(y=np.mean(data), c='tab:blue', ls='--')

                # plot outliers
                highs = np.array([[t, ep_data[t]] for t in range(len(ep_data)) if ep_data[t] >= high_limit])
                if len(highs.shape) == 2:
                    ax.scatter(highs[:, 0], highs[:, 1], marker='o', s=MARKER_SIZE, c=MAX_ELEM_COLOR, zorder=100)
                lows = np.array([[t, ep_data[t]] for t in range(len(ep_data)) if ep_data[t] <= low_limit])
                if len(lows.shape) == 2:
                    ax.scatter(lows[:, 0], lows[:, 1], marker='o', s=MARKER_SIZE, c=MIN_ELEM_COLOR, zorder=100)

                ax.set_xlim(0, len(ep_data))
                ax.yaxis.grid(True, which='both', linestyle='--', color='lightgrey')

            fig.suptitle(f'{title} Across {eps_per_plot} Episodes', fontweight='bold', fontsize=TITLE_FONT_SIZE)
            fig.subplots_adjust(wspace=1 / len(plot_eps_data), hspace=0)
            axs[0].set_ylabel(y_label, fontweight='bold')

            leg = fig.legend(labels=[y_label, high_label, low_label, 'Overall mean'], ncol=4,
                             fancybox=False, loc='upper center', borderaxespad=1.5)
            leg.get_frame().set_edgecolor('black')
            leg.get_frame().set_linewidth(0.8)

            plt.savefig(output_img, pad_inches=0, bbox_inches='tight')
            plt.close()

        #
        # ax.set_xlim(0, len(self.data))
        # format_and_save_plot(ax, title, output_img, 'Timesteps', y_label)

    def _plot_action_factor_divs(self, divs, output_img, title, y_label):

        plt.figure()
        ax = plt.gca()

        num_factors = divs.shape[0]
        colors = distinct_colors(num_factors)
        ax.bar(np.arange(num_factors), divs, color=colors, edgecolor='black', linewidth=0.7, zorder=100)
        plt.xticks(np.arange(num_factors), self.data[0].action_factors, rotation=45, horizontalalignment='right')

        format_and_save_plot(ax, title, output_img, '', y_label, False)
        plt.close()

    def _save_time_dataset_csv(self, element_data, dimension, file_name):
        ep = -1
        ep_t = 0
        data = OrderedDict({EPISODE_STR: [], TIME_STEP_STR: [], dimension: []})
        for t, datapoint in enumerate(self.data):
            if datapoint.new_episode or ep == -1:  # make sure we increment ep in first step
                ep += 1
                ep_t = 0
            data[EPISODE_STR].append(ep)
            data[TIME_STEP_STR].append(ep_t)
            data[dimension].append(element_data[t])
            ep_t += 1

        df = pd.DataFrame.from_dict(data)
        df.to_csv(file_name, index=False)
        logging.info(f'Saved CSV file with data for dimension "{dimension}" at {file_name}.')
