import io
import base64
import pandas as pd
from matplotlib import pyplot as plt
from flask import Flask, request, render_template, Response
from at_bat.game_parser import GameParser
from at_bat.plotter import Plotter

class Server:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'root', self.root, methods=['GET'])
        self.app.add_url_rule('/<int:gamepk>', 'gamepk', self.gamepk, methods=['GET'])

    def root(self):
        return Response('welcome', status=200, mimetype='text/plain')

    def gamepk(self, gamepk: int):
        settings = request.args.get('s', default='u')

        df = GameParser(gamepk=gamepk).dataframe

        if settings in ('u', 'ump', 'umpire'):
            if len(df) == 0:
                return Response('No missed calls', status=200, mimetype='text/plain')

            df = df.loc[
                (df['run_favor'] != 0) &
                ~(pd.isna(df['run_favor']))
            ]

            if len(df) == 0:
                return Response('No missed calls', status=200, mimetype='text/plain')

            new_row = pd.DataFrame([{
                'inning': 0,
                'run_favor': df['run_favor'].sum(),
                'wp_favor': df['wp_favor'].sum()
            }])
            df = pd.concat([new_row, df], ignore_index=True)

            df = df[['inning', 'is_top_inning', 'pitcher', 'batter', 'balls', 'strikes', 'outs', 'pitch_result_code', 'run_favor', 'wp_favor', 'px', 'pz', 'sz_top', 'sz_bot']]

        # if settings in ('bb', 'batted_ball'):
        #     df = df.loc[
        #         ~(pd.isna(df['batted_ball_launch_speed']))
        #     ]

        #     df = df[['inning', 'is_top_inning', 'batter', 'pitcher', 'balls', 'strikes', 'outs', 'batted_ball_launch_speed', 'batted_ball_launch_angle', 'batted_ball_total_distance', 'batted_ball_xba', 'batted_ball_xslg', 'px', 'pz', 'sz_top', 'sz_bot']]


        html_table = (
            df.to_html(
                classes="table table-striped table-bordered",
                # index=False,
                border=5,              # drop the default border attribute
            )
        )

        plotter = Plotter(missed_calls=df)
        buf = io.BytesIO()
        plotter.fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img_data = base64.b64encode(buf.getvalue()).decode('ascii')

        return render_template("gamepk.html", table=html_table, plot_data=img_data)

server = Server()
app = server.app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
