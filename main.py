import os
import numpy as np
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objs as go

def simulate_gacha(p: float, n_sims: int) -> np.ndarray:
  """
  p: 1回あたりのSSRの排出確率 (0 < p <= 1)
  n_sims: シミュレーション回数
  戻り値: 初SSRが出るまでの回数の配列
  """
  if p <= 0 or p > 1:
    raise ValueError("確率 p は 0 < p <= 1 で指定してください")
  return np.random.geometric(p, n_sims)

app = Dash(__name__)
app.title = "ガチャ期待値＆爆死シミュレーター"

app.layout = html.Div(
  style={"maxWidth": "800px", "margin": "auto", "fontFamily": "system-ui"},
  children=[
    html.H1("ガチャ期待値＆爆死シミュレーター"),
    html.P("SSRの排出率や課金額を変えて、爆死リスクを可視化してみよう。"),

    html.Hr(),

    html.Div(
      style={"display": "flex", "gap": "2rem", "flexWrap": "wrap"},
      children=[
        html.Div(
          style={"flex": "1 1 250px"},
          children=[
            html.Label("SSR排出率 (%)"),
            dcc.Slider(
              id="prob-slider",
              min=0.1,
              max=10,
              step=0.1,
              value=3,
              marks={0.1: "0.1", 1: "1", 3: "3", 5: "5", 10: "10"},
              tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Br(),

            html.Label("1回あたりの課金額 (円)"),
            dcc.Input(id="cost-input", type="number", value=300, min=1, step=10, style={"width": "100%"}),
            html.Br(), html.Br(),

            html.Label("シミュレーション回数"),
            dcc.Slider(
              id="nsims-slider",
              min=1000,
              max=50000,
              step=1000,
              value=10000,
              marks={1000: "1k", 10000: "10k", 50000: "50k"},
              tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Br(),

            html.Label("爆死とみなす上限回数"),
            dcc.Input( id="hardcap-input", type="number", value=200, min=1, step=10, style={"width": "100%"} ),
            html.Br(),
            html.Br(),

            html.Button("シミュレーション実行", id="run-button"),
            html.Div(id="error-msg", style={"color": "red", "marginTop": "0.5rem"}),
          ]
        ),
        html.Div(
          style={"flex": "1 1 300px"},
          children=[html.H3("統計まとめ"), html.Div(id="stats-output")]
        )
      ]
    ),

    html.Hr(),
    html.H3("SSRが初めて出るまでに必要な回数の分布"),
    dcc.Graph(id="hist-graph"),
  ]
)

@app.callback(
  [Output("hist-graph", "figure"), Output("stats-output", "children"), Output("error-msg", "children")],
  [Input("run-button", "n_clicks")],
  [
    State("prob-slider", "value"),
    State("cost-input", "value"),
    State("nsims-slider", "value"),
    State("hardcap-input", "value")
  ],
  prevent_initial_call=True
)

def update_simulation(n_clicks, prob_percent, cost_yen, n_sims, hardcap):
  """
  ガチャの確率シミュレーションを実行し、結果を表示用データに変換するコールバック関数。

  Dash の Callback から呼び出され、
  入力値（排出率・課金額・試行回数・爆死ライン）をもとに
  ガチャの試行シミュレーションを実行し、以下を計算します。

  - SSRが出るまでの回数の分布
  - 平均・中央値・90パーセンタイル
  - 想定課金額
  - 指定回数でSSRが出ない確率（爆死確率）

  Parameters
  ----------
  n_clicks : int or None
    「シミュレーション実行」ボタンが押された回数（Dash制御用）
  prob_percent : float
    SSR排出率（%表示）
  cost_yen : int
    1回あたりのガチャ金額（円）
  n_sims : int
    シミュレーション回数
  hardcap : int
    爆死判定回数（この回数引いても出ない確率を算出）

  Returns
  -------
  tuple
    (グラフ用 Figure, 統計表示用コンポーネント, エラーメッセージ文字列)
  """
  # エラーチェック
  if not prob_percent or prob_percent <= 0:
    return go.Figure(), "", "排出率は 0 より大きくしてください。"
  if not cost_yen or cost_yen <= 0:
    return go.Figure(), "", "ガチャ金額は 0 より大きくしてください。"
  if not n_sims or n_sims <= 0:
    return go.Figure(), "", "シミュレーション回数は 0 より大きくしてください。"

  p = prob_percent / 100

  try:
    trials = simulate_gacha(p, n_sims)
  except ValueError as e:
    return go.Figure(), "", str(e)

  # 統計値
  mean_trials = float(np.mean(trials))
  median_trials = float(np.median(trials))
  p90_trials = float(np.quantile(trials, 0.9))

  mean_cost = mean_trials * cost_yen
  median_cost = median_trials * cost_yen
  p90_cost = p90_trials * cost_yen

  # 爆死確率(hardcap 回回しても出ない確率 ≒ (1 - p)^hardcap)
  bust_prob = (1 - p) ** hardcap if hardcap and hardcap > 0 else None

  status_text = [
    html.P(f"シミュレーション回数: {n_sims:,} 回"),
    html.P(f"SSR排出率: {prob_percent:.2f} %"),
    html.P(f"期待されるガチャ回数(平均): {mean_trials:.1f} 回 ≒ {mean_cost:,.0f} 円"),
    html.P(f"中央値: {median_trials:.1f} 回 ≒ {median_cost:,.0f} 円"),
    html.P(f"90%の人がこの回数までには出る: {p90_trials:.1f} 回 ≒ {p90_cost:,.0f} 円"),
  ]

  if bust_prob:
    status_text.append(html.P(f"{hardcap} 回回してもSSRが出ない確率: {bust_prob * 100:.2f} %"))

  # ヒストグラム(長すぎる尻尾はある程度切る)
  max_display = int(np.percentile(trials, 99.9))
  clipped = trials[trials <= max_display]

  hist = go.Histogram(x=trials, xbins=dict(start=0.5, end=max_display + 0.5, size=1))

  layout = go.Layout(xaxis_title="SSRが初めて出るまでのガチャ回数", yaxis_title="頻度", bargap=0.05)

  fig = go.Figure(data=[hist], layout=layout)

  return fig, status_text, ""

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8050))
  app.run(
    debug=False,          # 本番なので False 推奨
    host="0.0.0.0",       # 外部からアクセスできるように
    port=port,
  )
