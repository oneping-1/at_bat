from matplotlib import pyplot as plt
from matplotlib import patches
import pandas as pd

class Plotter:
    px_min = -17/2/12
    px_max = 17/2/12
    pz_min = 1.5
    pz_max = 3.5
    radius = .1208

    def __init__(self, missed_calls: pd.DataFrame):
        self.missed_calls = missed_calls

        self.fig, self.axis = plt.subplots()

        self._create_plot()

        for i, row in self.missed_calls.iterrows():
            self._print_pitch(i, row)

        # plt.show()


    def _create_plot(self):
        _width = self.px_max - self.px_min
        _height = self.pz_max - self.pz_min
        strike_zone = patches.Rectangle((self.px_min, self.pz_min), _width, _height,
            facecolor='none', edgecolor='black')

        self.axis.add_patch(strike_zone)

        plt.xlim([-1.5, 1.5])
        plt.ylim([1, 4])
        self.axis.set_aspect('equal')


    def _print_pitch(self, i: int, row: pd.Series):
        pitch_color = _pitch_color(row['pitch_result_code'])

        px = row['px']
        pz = row['pz']
        sz_min = row['sz_bot']
        sz_max = row['sz_top']

        pz = self._normalize_pitch_height(pz, sz_min, sz_max)

        pitch = patches.Circle((px, pz), self.radius, facecolor='none', edgecolor=pitch_color)
        self.axis.add_patch(pitch)

        self.axis.text(px, pz, str(i), ha='center', va='center')

    def _normalize_pitch_height(self, pz: float, sz_min: float, sz_max: float) -> float:
        """
        Normalize pitch height to standard 1.5 or 3.5 feet off ground.
        This is so that the top and bottom of the strike zone is
        consistance for all pitches shown since. Without this function
        it would be impossible to tell where a pitch was relaive to the
        zone since the top and bottom changes every pitch

        Args:
            pz (float): location of the pitch
            sz_min (float): bottom of the strike zone
            sz_max (float): top of the strike zone

        Returns:
            float: normalized pitch location
        """
        to_top = pz - sz_max
        to_bot = pz - sz_min

        if abs(to_top) >= abs(to_bot):
            return self.pz_min + to_bot
        return self.pz_max + to_top

def _pitch_color(pitch_result_code: str):
    if pitch_result_code == 'B':
        return 'green'
    if pitch_result_code == 'C':
        return 'red'
    return 'black'

def _filter_df(dataframe: pd.DataFrame):
    if len(dataframe) == 0:
        return pd.DataFrame()

    dataframe = dataframe.loc[
        (dataframe['run_favor'] != 0) &
        ~(pd.isna(dataframe['run_favor']))
    ]

    if len(dataframe) == 0:
        return pd.DataFrame()

    new_row = pd.DataFrame([{
        'inning': 0,
        'run_favor': dataframe['run_favor'].sum(),
        'wp_favor': dataframe['wp_favor'].sum()
    }])
    dataframe = pd.concat([new_row, dataframe], ignore_index=True)

    dataframe = dataframe[[
        'inning',
        'is_top_inning',
        'pitcher',
        'batter',
        'balls',
        'strikes',
        'outs',
        'pitch_result_code',
        'run_favor',
        'wp_favor',
        'px',
        'pz',
        'sz_bot',
        'sz_top',
        ]]

    return dataframe

if __name__ == '__main__':
    from at_bat.game_parser import GameParser
    game = GameParser(gamepk=777777)
    df = game.dataframe
    df = _filter_df(df)

    plotter = Plotter(df)
