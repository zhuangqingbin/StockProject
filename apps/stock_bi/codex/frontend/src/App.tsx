import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { MarketShell } from "./features/market-overview/MarketShell";

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app-shell">
        <div className="app-shell__backdrop" aria-hidden="true" />
        <MarketShell />
      </div>
    </QueryClientProvider>
  );
};

export default App;
