import pandas as pd
from flask import Flask, request, render_template, Response
from at_bat.game_parser import GameParser

class Server:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/<int:gamepk>', 'gamepk', self.gamepk, methods=['GET'])

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

            new_row = {
                'run_favor': df['run_favor'].sum(),
                'wp_favor': df['wp_favor'].sum()
            }
            df.loc[len(df)] = new_row
            df.reset_index(inplace=True)

            df = df[['inning', 'is_top_inning', 'pitcher', 'batter', 'balls', 'strikes', 'outs', 'pitch_result_code', 'run_favor', 'wp_favor']]

        if settings in ('bb', 'batted_ball'):
            df = df.loc[
                ~(pd.isna(df['batted_ball_launch_speed']))
            ]

            df = df[['inning', 'is_top_inning', 'batter', 'pitcher', 'balls', 'strikes', 'outs', 'batted_ball_launch_speed', 'batted_ball_launch_angle', 'batted_ball_total_distance', 'batted_ball_xba', 'batted_ball_xslg']]

        html_table = (
            df.to_html(
                classes="table table-striped table-bordered",
                # index=False,
                border=5,              # drop the default border attribute
            )
        )

        return render_template("gamepk.html", table=html_table)

server = Server()
app = server.app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
