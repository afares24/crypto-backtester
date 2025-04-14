use axum::{routing::post, Router, Json};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use ta::indicators::RelativeStrengthIndex;
use ta::indicators::SimpleMovingAverage;
use ta::indicators::MovingAverageConvergenceDivergence as Macd;
use ta::indicators::BollingerBands;

use ta::Next;

#[derive(Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
enum TradeLogic {
    All,
    Any,
}

#[derive(Deserialize)]
struct Payload {
    symbol: String,
    interval: String,
    start_date: Option<String>,
    end_date: Option<String>,
    price_data: Vec<PriceRecord>,
    indicators: Indicators,
    trade_logic: TradeLogic,
    take_profit: f64,
    stop_loss: f64,
}

#[derive(Deserialize)]
struct PriceRecord {
    Date: String,
    Open: f64,
    High: f64,
    Low: f64,
    Close: f64,
    Volume: f64,
}

#[derive(Deserialize)]
struct Indicators {
    rsi: RSISettings,
    sma: SMASettings,
    macd: MACDSettings,
    bbands: BBandSettings,
}

#[derive(Deserialize)]
struct BBandSettings {
    enabled: bool,
    period: Option<u32>,
    std_dev: Option<f64>,
}

#[derive(Deserialize)]
struct RSISettings {
    enabled: bool,
    period: Option<u32>,
    overbought: Option<f64>,
    oversold: Option<f64>,
}

#[derive(Deserialize)]
struct SMASettings {
    enabled: bool,
    period: Option<u32>,
}

#[derive(Deserialize)]
struct MACDSettings {
    enabled: bool,
    fast: Option<u32>,
    slow: Option<u32>,
    signal: Option<u32>,
}

#[derive(Serialize)]
struct StrategyResult {
    roi: f64,
    rsi_values: Vec<RSIResult>,
    chart_data: Vec<ChartData>,
}

#[derive(Serialize)]
struct RSIResult {
    date: String,
    rsi: f64,
}

#[derive(Serialize)]
struct ChartData {
    date: String,
    close: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    rsi: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    sma: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    macd: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    macd_signal: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    bb_upper: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    bb_lower: Option<f64>,
}

async fn strategy_handler(Json(payload): Json<Payload>) -> Json<StrategyResult> {
    let mut rsi_values = Vec::new();
    let mut chart_data = Vec::new();

    let mut sma_opt = None;
    if payload.indicators.sma.enabled {
        let period = payload.indicators.sma.period.unwrap_or(20);
        sma_opt = Some(SimpleMovingAverage::new(period.try_into().unwrap()).unwrap());
    }

    let mut macd_opt = None;
    if payload.indicators.macd.enabled {
        let fast = payload.indicators.macd.fast.unwrap_or(12);
        let slow = payload.indicators.macd.slow.unwrap_or(26);
        let signal = payload.indicators.macd.signal.unwrap_or(9);
        macd_opt = Some(Macd::new(fast.try_into().unwrap(), slow.try_into().unwrap(), signal.try_into().unwrap()).unwrap());
    }

    let mut bbands_opt = None;
    if payload.indicators.bbands.enabled {
        let period = payload.indicators.bbands.period.unwrap_or(20);
        let std_dev = payload.indicators.bbands.std_dev.unwrap_or(2.0);
        bbands_opt = Some(BollingerBands::new(period.try_into().unwrap(), std_dev).unwrap());
    }

    let mut rsi = if payload.indicators.rsi.enabled {
        Some(RelativeStrengthIndex::new(payload.indicators.rsi.period.unwrap_or(14).try_into().unwrap()).unwrap())
    } else {
        None
    };

    for record in &payload.price_data {
        let mut rsi_val = None;
        let mut sma_val = None;
        let mut macd_val = None;
        let mut macd_sig_val = None;
        let mut bb_upper = None;
        let mut bb_lower = None;

        if let Some(ind) = &mut rsi {
            let v = ind.next(record.Close);
            rsi_values.push(RSIResult {
                date: record.Date.clone(),
                rsi: v,
            });
            rsi_val = Some(v);
        }

        if let Some(ind) = &mut sma_opt {
            sma_val = Some(ind.next(record.Close));
        }

        if let Some(ind) = &mut macd_opt {
            let macd_result = ind.next(record.Close);
            macd_val = Some(macd_result.macd);
            macd_sig_val = Some(macd_result.signal);
        }

        if let Some(ind) = &mut bbands_opt {
            let bands = ind.next(record.Close);
            bb_upper = Some(bands.upper);
            bb_lower = Some(bands.lower);
        }

        chart_data.push(ChartData {
            date: record.Date.clone(),
            close: record.Close,
            rsi: rsi_val,
            sma: sma_val,
            macd: macd_val,
            macd_signal: macd_sig_val,
            bb_upper,
            bb_lower,
        });
    }

    let sma_enabled = payload.indicators.sma.enabled;
    let rsi_enabled = payload.indicators.rsi.enabled;
    let macd_enabled = payload.indicators.macd.enabled;

    let mut position_open = false;
    let mut entry_price = 0.0;
    let mut balance = 1.0;

    for i in 1..chart_data.len() {
        let prev = &chart_data[i - 1];
        let curr = &chart_data[i];

        let buy_sma = if sma_enabled {
            if let (Some(sma_prev), Some(sma_curr)) = (prev.sma, curr.sma) {
                (prev.close < sma_prev) && (curr.close > sma_curr)
            } else {
                false
            }
        } else {
            true
        };

        let buy_rsi = if rsi_enabled {
            if let (Some(rsi_prev), Some(rsi_curr)) = (prev.rsi, curr.rsi) {
                let oversold = payload.indicators.rsi.oversold.unwrap_or(30.0);
                (rsi_prev < oversold) && (rsi_curr > oversold)
            } else {
                false
            }
        } else {
            true
        };

        let buy_macd = if macd_enabled {
            if let (Some(macd_prev), Some(macd_curr)) = (prev.macd, curr.macd) {
                if let (Some(sig_prev), Some(sig_curr)) = (prev.macd_signal, curr.macd_signal) {
                    (macd_prev < sig_prev) && (macd_curr > sig_curr)
                } else {
                    false
                }
            } else {
                false
            }
        } else {
            true
        };

        let mut buy_signals = vec![];
        if sma_enabled {
            buy_signals.push(buy_sma);
        }
        if rsi_enabled {
            buy_signals.push(buy_rsi);
        }
        if macd_enabled {
            buy_signals.push(buy_macd);
        }
        let buy_signal = if buy_signals.is_empty() {
            false
        } else if payload.trade_logic == TradeLogic::All {
            buy_signals.iter().all(|&x| x)
        } else {
            buy_signals.iter().any(|&x| x)
        };

        let sell_sma = if sma_enabled {
            if let (Some(sma_prev), Some(sma_curr)) = (prev.sma, curr.sma) {
                (prev.close > sma_prev) && (curr.close < sma_curr)
            } else {
                false
            }
        } else {
            true
        };

        let sell_rsi = if rsi_enabled {
            if let (Some(rsi_prev), Some(rsi_curr)) = (prev.rsi, curr.rsi) {
                let overbought = payload.indicators.rsi.overbought.unwrap_or(70.0);
                (rsi_prev > overbought) && (rsi_curr < overbought)
            } else {
                false
            }
        } else {
            true
        };

        let sell_macd = if macd_enabled {
            if let (Some(macd_prev), Some(macd_curr)) = (prev.macd, curr.macd) {
                if let (Some(sig_prev), Some(sig_curr)) = (prev.macd_signal, curr.macd_signal) {
                    (macd_prev > sig_prev) && (macd_curr < sig_curr)
                } else {
                    false
                }
            } else {
                false
            }
        } else {
            true
        };

        let mut sell_signals = vec![];
        if sma_enabled {
            sell_signals.push(sell_sma);
        }
        if rsi_enabled {
            sell_signals.push(sell_rsi);
        }
        if macd_enabled {
            sell_signals.push(sell_macd);
        }
        let sell_signal = if sell_signals.is_empty() {
            false
        } else if payload.trade_logic == TradeLogic::All {
            sell_signals.iter().all(|&x| x)
        } else {
            sell_signals.iter().any(|&x| x)
        };

        if !position_open && buy_signal {
            position_open = true;
            entry_price = curr.close;
        } else if position_open {
            let gain = (curr.close - entry_price) / entry_price;

            if gain >= payload.take_profit / 100.0 || gain <= -payload.stop_loss / 100.0 {
                position_open = false;
                balance = balance * (curr.close / entry_price);
                continue;
            }

            if sell_signal {
                position_open = false;
                let exit_price = curr.close;
                balance = balance * (exit_price / entry_price);
            }
        }
    }

    if position_open {
        let last = chart_data.last().unwrap();
        balance = balance * (last.close / entry_price);
        position_open = false;
    }

    let roi = balance - 1.0;

    let result = StrategyResult {
        roi,
        rsi_values,
        chart_data,
    };

    Json(result)
}

#[tokio::main]
async fn main() {
    let app = Router::new().route("/strategy", post(strategy_handler));

    let addr = SocketAddr::from(([127, 0, 0, 1], 8001));
    println!("Listening on {}", addr);

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}