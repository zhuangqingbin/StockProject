import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChatConsole } from "../../../features/chat-console/ChatConsole";
import { useDashboardStore } from "../../../lib/state/dashboardStore";

vi.mock("../../../lib/api/chatApi", () => ({
  queryAssistant: vi.fn(),
}));

const { queryAssistant } = await import("../../../lib/api/chatApi");

describe("ChatConsole", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDashboardStore.setState({
      activeStock: null,
      activeIndustry: null,
      order: "desc",
      rankingSortBy: "pct_chg",
      topN: 10,
      updateBannerTradeDate: null,
      view: "distribution",
      wsStatus: "connected",
    });
  });

  it("allows typing without auto-submitting", async () => {
    const user = userEvent.setup();

    vi.mocked(queryAssistant).mockResolvedValue({
      reply: "已收到",
      data: null,
      chart_config: null,
      sql: null,
    });

    render(<ChatConsole />);

    const input = screen.getByPlaceholderText("问我今天市场发生了什么，或者要哪类股票。");
    await user.type(input, "北向资金今天怎么看");

    expect(input).toHaveValue("北向资金今天怎么看");
    expect(queryAssistant).not.toHaveBeenCalled();
  });

  it("submits on Enter but keeps Shift+Enter for multiline drafting", async () => {
    const user = userEvent.setup();

    vi.mocked(queryAssistant).mockResolvedValue({
      reply: "这是分析结果",
      data: null,
      chart_config: null,
      sql: null,
    });

    render(<ChatConsole />);

    const input = screen.getByPlaceholderText("问我今天市场发生了什么，或者要哪类股票。");
    await user.type(input, "第一行");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(input, "第二行");

    expect(input).toHaveValue("第一行\n第二行");
    expect(queryAssistant).not.toHaveBeenCalled();

    await user.keyboard("{Enter}");

    expect(queryAssistant).toHaveBeenCalledWith(
      "第一行\n第二行",
      expect.arrayContaining([
        expect.objectContaining({
          role: "assistant",
        }),
      ]),
    );
    expect(await screen.findByText("这是分析结果")).toBeInTheDocument();
  });
});
