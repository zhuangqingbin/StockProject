import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useDashboardStore } from "../state/dashboardStore";

const RECONNECT_DELAY_MS = 5000;

export const buildMarketSocketUrl = (source?: Pick<Location, "protocol" | "host">) => {
  const locationSource = source ?? window.location;
  const protocol = locationSource.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${locationSource.host}/ws/market`;
};

export const useMarketSocket = () => {
  const queryClient = useQueryClient();
  const setWsStatus = useDashboardStore((state) => state.setWsStatus);
  const setUpdateBannerTradeDate = useDashboardStore((state) => state.setUpdateBannerTradeDate);

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }

    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let disposed = false;

    const connect = () => {
      setWsStatus("connecting");
      socket = new WebSocket(buildMarketSocketUrl());

      socket.onopen = () => {
        setWsStatus("connected");
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { type?: string; trade_date?: string };

        if (payload.type === "data_updated" && payload.trade_date) {
          setUpdateBannerTradeDate(payload.trade_date);
          queryClient.invalidateQueries({ queryKey: ["market"] });
        }

        if (payload.type === "connected") {
          setWsStatus("connected");
        }
      };

      socket.onclose = () => {
        setWsStatus("disconnected");
        if (!disposed) {
          reconnectTimer = window.setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };

      socket.onerror = () => {
        setWsStatus("disconnected");
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [queryClient, setUpdateBannerTradeDate, setWsStatus]);
};
