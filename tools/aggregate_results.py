#!/usr/bin/env python3
import argparse
import os
import pandas as pd
from typing import Dict


def load_csvs(log_dir: str) -> Dict[str, pd.DataFrame]:
    dfs = {}
    for proto in ["mqtt", "coap", "http"]:
        pdir = os.path.join(log_dir, proto)
        if not os.path.isdir(pdir):
            continue
        for name in os.listdir(pdir):
            if name.endswith(".csv"):
                key = f"{proto}/{name}"
                dfs[key] = pd.read_csv(os.path.join(pdir, name))
    return dfs


def merge_mqtt(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    pubs = [v for k, v in dfs.items() if k.startswith("mqtt/") and "publisher" in k]
    subs = [v for k, v in dfs.items() if k.startswith("mqtt/") and "subscriber" in k]
    if not pubs or not subs:
        return pd.DataFrame()
    pub = pd.concat(pubs, ignore_index=True)
    sub = pd.concat(subs, ignore_index=True)
    pub = pub.rename(columns={"bytes_sent_sender_to_receiver": "bytes_pub"})
    sub = sub.rename(columns={"bytes_sent_sender_to_receiver": "bytes_sub"})
    # Join on seq_id
    merged = pd.merge(pub, sub[["seq_id", "file_name", "t_start_ns", "bytes_sub"]], on=["seq_id", "file_name"], how="inner", suffixes=("_pub", "_sub"))
    # Receiver time as sub.t_start_ns; compute latency and throughput
    merged["end_ns_receiver"] = merged["t_start_ns_sub"]
    merged["duration_ms"] = (merged["end_ns_receiver"] - merged["t_start_ns_pub"]) / 1e6
    merged["throughput_bps"] = merged["file_size_bytes_pub"] * 8 / (merged["duration_ms"] / 1000.0).clip(lower=1e-9)
    merged["sender_to_receiver_bytes"] = merged["bytes_pub"] + merged["bytes_sub"]
    merged["overhead_ratio"] = merged["sender_to_receiver_bytes"] / merged["file_size_bytes_pub"].replace(0, pd.NA)
    return merged


def summarize(df: pd.DataFrame, label_file_size_col: str) -> pd.DataFrame:
    if df.empty:
        return df
    df["file_size"] = df[label_file_size_col]
    summary = df.groupby(["protocol_pub" if "protocol_pub" in df.columns else "protocol", "file_name"]).agg(
        count=("seq_id", "count"),
        avg_ms=("duration_ms", "mean"),
        median_ms=("duration_ms", "median"),
        p95_ms=("duration_ms", lambda s: s.quantile(0.95)),
        avg_throughput_bps=("throughput_bps", "mean") if "throughput_bps" in df.columns else ("file_size_bytes", "mean"),
        avg_overhead_ratio=("overhead_ratio", "mean") if "overhead_ratio" in df.columns else ("bytes_sent_sender_to_receiver", "mean"),
    ).reset_index()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", default="logs")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    dfs = load_csvs(args.logs)

    mqtt = merge_mqtt(dfs)

    # CoAP and HTTP just concatenate client and server for summaries; use client timing for E2E
    coap_client = dfs.get("coap/client.csv")
    http_client = dfs.get("http/client.csv")

    with pd.ExcelWriter(args.out, engine="openpyxl") as writer:
        if not mqtt.empty:
            mqtt["throughput_bps"] = mqtt["throughput_bps"].astype(float)
            mqtt["overhead_ratio"] = mqtt["overhead_ratio"].astype(float)
            mqtt.to_excel(writer, sheet_name="MQTT_Events", index=False)
            summarize(mqtt, "file_size_bytes_pub").to_excel(writer, sheet_name="MQTT_Summary", index=False)
        if coap_client is not None and not coap_client.empty:
            coap_df = coap_client.copy()
            coap_df["throughput_bps"] = coap_df["file_size_bytes"] * 8 / (coap_df["duration_ms"] / 1000.0).clip(lower=1e-9)
            coap_df["overhead_ratio"] = coap_df["bytes_sent_sender_to_receiver"] / coap_df["file_size_bytes"].replace(0, pd.NA)
            coap_df.to_excel(writer, sheet_name="CoAP_Events", index=False)
            summarize(coap_df, "file_size_bytes").to_excel(writer, sheet_name="CoAP_Summary", index=False)
        if http_client is not None and not http_client.empty:
            http_df = http_client.copy()
            http_df["throughput_bps"] = http_df["file_size_bytes"] * 8 / (http_df["duration_ms"] / 1000.0).clip(lower=1e-9)
            http_df["overhead_ratio"] = http_df["bytes_sent_sender_to_receiver"] / http_df["file_size_bytes"].replace(0, pd.NA)
            http_df.to_excel(writer, sheet_name="HTTP_Events", index=False)
            summarize(http_df, "file_size_bytes").to_excel(writer, sheet_name="HTTP_Summary", index=False)

    # Also write CSV summaries
    base = os.path.splitext(args.out)[0]
    if not mqtt.empty:
        mqtt.to_csv(f"{base}_mqtt_events.csv", index=False)
        summarize(mqtt, "file_size_bytes_pub").to_csv(f"{base}_mqtt_summary.csv", index=False)
    if coap_client is not None and not coap_client.empty:
        coap_df = coap_client.copy()
        coap_df["throughput_bps"] = coap_df["file_size_bytes"] * 8 / (coap_df["duration_ms"] / 1000.0).clip(lower=1e-9)
        coap_df["overhead_ratio"] = coap_df["bytes_sent_sender_to_receiver"] / coap_df["file_size_bytes"].replace(0, pd.NA)
        coap_df.to_csv(f"{base}_coap_events.csv", index=False)
        summarize(coap_df, "file_size_bytes").to_csv(f"{base}_coap_summary.csv", index=False)
    if http_client is not None and not http_client.empty:
        http_df = http_client.copy()
        http_df["throughput_bps"] = http_df["file_size_bytes"] * 8 / (http_df["duration_ms"] / 1000.0).clip(lower=1e-9)
        http_df["overhead_ratio"] = http_df["bytes_sent_sender_to_receiver"] / http_df["file_size_bytes"].replace(0, pd.NA)
        http_df.to_csv(f"{base}_http_events.csv", index=False)
        summarize(http_df, "file_size_bytes").to_csv(f"{base}_http_summary.csv", index=False)


if __name__ == "__main__":
    main()
