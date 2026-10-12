import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Chat } from "@/components/chat";
import { ApiError } from "@/lib/api";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  fetchModels: jest.fn(),
  streamChat: jest.fn(),
}));

const mocked = api as jest.Mocked<typeof api>;

beforeEach(() => {
  mocked.fetchModels.mockResolvedValue([
    { id: "nova-micro", display_name: "Amazon Nova Micro", provider: "amazon", tier: "small" },
  ]);
});

describe("Chat", () => {
  it("shows the empty state and keeps submit disabled until there is a prompt", async () => {
    render(<Chat />);
    expect(screen.getByText("Nothing has been drunk yet.")).toBeInTheDocument();
    const button = screen.getByRole("button", { name: "Ask the model" });
    expect(button).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Prompt"), "hello");
    expect(await screen.findByRole("option", { name: "Amazon Nova Micro" })).toBeInTheDocument();
    expect(button).toBeEnabled();
    expect(screen.getByText("5 / 2,000")).toBeInTheDocument();
  });

  it("shows the streamed answer and the metrics", async () => {
    mocked.streamChat.mockImplementation(async ({ onToken }) => {
      onToken("Rain");
      return {
        model: "nova-micro",
        input_tokens: 5,
        output_tokens: 7,
        cost_usd: 0.00041,
        latency_ms: 1200,
        ttft_ms: 300,
        tokens_per_sec: 12,
        footprint: { energy_wh: 0.15, carbon_g: 0.03, water_l: 0.0008 },
        equivalents: [
          { kind: "water_sips", value: 16, unit: "drops of water", label: "16 drops of water" },
        ],
      };
    });
    render(<Chat />);
    await screen.findByRole("option", { name: "Amazon Nova Micro" });
    await userEvent.type(screen.getByLabelText("Prompt"), "why rain");
    await userEvent.click(screen.getByRole("button", { name: "Ask the model" }));
    expect(await screen.findByText("Rain")).toBeInTheDocument();
    expect(await screen.findByText("$0.00041")).toBeInTheDocument();
    expect(screen.getByText("1.2 s")).toBeInTheDocument();
    expect(screen.getByText("16")).toBeInTheDocument();
  });

  it("shows a clear message for a spend-cap 429", async () => {
    mocked.streamChat.mockRejectedValue(new ApiError("spend_cap", api.messageFor("spend_cap")));
    render(<Chat />);
    await screen.findByRole("option", { name: "Amazon Nova Micro" });
    await userEvent.type(screen.getByLabelText("Prompt"), "hi");
    await userEvent.click(screen.getByRole("button", { name: "Ask the model" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("used up today's budget");
  });
});
