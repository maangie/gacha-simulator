import numpy as np
import pytest

from main import simulate_gacha, update_simulation


def stat_lines(stats):
  """
  統計表示用コンポーネントのリストから、各行のテキストを取り出す。

  Parameters
  ----------
  stats : list
    `html.P` コンポーネントのリスト

  Returns
  -------
  list[str]
    各行のテキスト
  """
  return [p.children for p in stats]


def run(prob_percent=3, cost_yen=300, n_sims=10000, hardcap=200):
  """
  乱数を固定して `update_simulation` を呼び出す。

  Parameters
  ----------
  prob_percent : float
    SSR排出率（%表示）
  cost_yen : int
    1回あたりのガチャ金額（円）
  n_sims : int
    シミュレーション回数
  hardcap : int or None
    爆死判定回数

  Returns
  -------
  tuple
    (グラフ用 Figure, 統計表示用コンポーネント, エラーメッセージ文字列)
  """
  np.random.seed(0)
  return update_simulation(1, prob_percent, cost_yen, n_sims, hardcap)


class TestSimulateGacha:
  """simulate_gacha の確率計算のテスト。"""

  def test_length_and_lower_bound(self):
    """戻り値の長さが n_sims と一致し、すべて 1 以上であること。"""
    np.random.seed(0)
    trials = simulate_gacha(0.03, 1000)
    assert len(trials) == 1000
    assert trials.min() >= 1

  def test_certain_probability(self):
    """p=1 なら全試行が 1 回目で出ること。"""
    assert (simulate_gacha(1, 100) == 1).all()

  def test_mean_is_close_to_expected(self):
    """平均が期待値 1/p に近いこと。"""
    np.random.seed(0)
    trials = simulate_gacha(0.03, 50000)
    assert trials.mean() == pytest.approx(1 / 0.03, rel=0.05)

  @pytest.mark.parametrize("p", [0, -0.1, 1.1])
  def test_invalid_probability(self, p):
    """0 以下・1 超の確率は ValueError になること。"""
    with pytest.raises(ValueError):
      simulate_gacha(p, 10)


class TestUpdateSimulation:
  """update_simulation の入力検証と表示内容のテスト。"""

  @pytest.mark.parametrize("kwargs", [
    {"prob_percent": 0},
    {"prob_percent": None},
    {"cost_yen": 0},
    {"cost_yen": None},
    {"n_sims": 0},
    {"n_sims": None},
  ])
  def test_invalid_input_returns_error(self, kwargs):
    """不正な入力ではエラーメッセージが返り、統計は空になること。"""
    _, stats, error = run(**kwargs)
    assert error != ""
    assert stats == ""

  def test_valid_input_has_no_error(self):
    """正しい入力ではエラーメッセージが空で、統計が表示されること。"""
    _, stats, error = run()
    assert error == ""
    assert any("期待されるガチャ回数" in line for line in stat_lines(stats))

  def test_bust_probability_shown(self):
    """爆死確率の行が (1-p)^hardcap の値で表示されること。"""
    _, stats, _ = run(hardcap=200)
    expected = f"{(1 - 0.03) ** 200 * 100:.2f} %"
    assert any(expected in line for line in stat_lines(stats))

  def test_bust_probability_shown_when_underflow(self):
    """確率がアンダーフローで 0.0 になっても、爆死確率の行が表示されること。"""
    assert (1 - 0.03) ** 100000 == 0.0
    _, stats, _ = run(hardcap=100000)
    assert any("0.00 %" in line for line in stat_lines(stats))

  @pytest.mark.parametrize("hardcap", [None, 0])
  def test_bust_probability_hidden_without_hardcap(self, hardcap):
    """爆死上限回数が未指定・0 なら、爆死確率の行が表示されないこと。"""
    _, stats, _ = run(hardcap=hardcap)
    assert not any("出ない確率" in line for line in stat_lines(stats))

  def test_histogram_clips_tail(self):
    """ヒストグラムには、99.9 パーセンタイルを超える裾が含まれないこと。"""
    fig, _, _ = run(n_sims=10000)
    x = fig.data[0].x
    assert len(x) < 10000
    assert max(x) <= fig.data[0].xbins.end
